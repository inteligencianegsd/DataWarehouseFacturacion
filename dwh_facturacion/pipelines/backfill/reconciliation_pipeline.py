"""
Reconciliacion Fenix -> Bronze para recuperar registros que el incremental regular
nunca va a recoger.

El incremental de cada tabla usa como watermark el MAX() de una columna de fecha en
Bronze (fecha_hora en facturas, fecha_act en clientes/vendedores). Si un registro llega
a Fenix "atrasado" respecto a ese watermark (retraso de replicacion, correccion con
fecha vieja), el incremental lo salta para siempre -- el watermark solo avanza.

Este pipeline compara, dentro de una ventana reciente (lookback_days), el conjunto de
claves que existen en Fenix contra el conjunto que ya esta en Bronze, y hace upsert de
lo que falte. No reemplaza el incremental regular: es una red de seguridad que corre
por separado (ver dwh_facturacion.tasks.run_backfill_*).

Del lado Fenix solo se miran claves hasta el watermark actual de Bronze (el mismo
MAX() que usa el incremental, via get_last_transaction_date). Lo que esta por encima
del watermark todavia le toca al incremental: si el backfill lo trajera, (1) lo
reportaria como "faltante" sin serlo y (2) adelantaria el watermark, haciendo que el
incremental salte filas que lleguen tarde con fecha anterior.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Type

import pandas as pd
from sqlalchemy import text, bindparam, or_

from dwh_facturacion.common.session_manager import get_session
from dwh_facturacion.etl.extract.db_extractor import DatabaseExtractor
from dwh_facturacion.etl.load.db_load import DWBatchedLoader
from dwh_facturacion.etl.transform.general_functions import CleanSpecialCharacters, DropDuplicatesTransform
from dwh_facturacion.utils.mode_persistence import ModePersistence


@dataclass(frozen=True)
class ReconciliationSpec:
    name: str
    # SELECT <fenix_key_col>, <fecha> AS fecha_ref ... FROM ...
    # WHERE <ventana> >= :cutoff AND <columna del incremental> <= :watermark
    fenix_key_set_query: str
    fenix_key_col: str
    # SELECT completo de una fila ... WHERE <key> = :<fenix_key_param>
    fenix_recover_query: str
    fenix_key_param: str
    bronze_entity: Type
    bronze_key_col: str
    bronze_window_col: str
    conflict_cols: tuple[str, ...]
    update_cols: tuple[str, ...]
    clean_special_chars_cols: tuple[str, ...] = field(default_factory=tuple)


class ReconciliationPipeline:
    def __init__(self, spec: ReconciliationSpec, lookback_days: int = 30):
        self.spec = spec
        self.lookback_days = lookback_days

    def _cutoff(self) -> dt.date:
        return dt.date.today() - dt.timedelta(days=self.lookback_days)

    def _watermark(self, db_alias: str):
        """Watermark actual del incremental de esta tabla en Bronze (None si vacia)."""
        with get_session(db_alias) as session:
            return self.spec.bronze_entity.get_last_transaction_date(session)

    def _fenix_keys(self, cutoff: dt.date, watermark) -> dict:
        """Claves de Fenix en la ventana, hasta el watermark:
        clave normalizada (como queda en Bronze) -> (clave cruda en Fenix, fecha_ref)."""
        df = DatabaseExtractor(
            db_alias="FENIX",
            query=self.spec.fenix_key_set_query,
            params={"cutoff": cutoff, "watermark": watermark},
        ).fit_transform(None)
        if df.empty:
            return {}
        key_col = self.spec.fenix_key_col
        raw = df[key_col].tolist()
        if key_col in self.spec.clean_special_chars_cols:
            df = CleanSpecialCharacters([key_col]).fit_transform(df)
        return {
            norm: (orig, fecha)
            for norm, orig, fecha in zip(df[key_col], raw, df["fecha_ref"])
        }

    def _bronze_keys(self, db_alias: str, cutoff: dt.date) -> set:
        entity = self.spec.bronze_entity
        key_attr = getattr(entity, self.spec.bronze_key_col)
        window_attr = getattr(entity, self.spec.bronze_window_col)
        with get_session(db_alias) as session:
            # Incluye las filas con la columna de ventana en NULL, igual que el lado Fenix
            # (clientes/vendedores con fecha_act NULL), para no reportarlas cada noche.
            rows = session.query(key_attr).filter(
                or_(window_attr >= cutoff, window_attr.is_(None))
            ).all()
        return {row[0] for row in rows}

    _RECOVER_BATCH_SIZE = 500

    def _recover(self, missing_keys: set) -> pd.DataFrame:
        """Trae de Fenix las filas completas de las claves que faltan en Bronze, en
        lotes de _RECOVER_BATCH_SIZE (WHERE ... IN :keys), para no depender de una
        consulta por clave cuando faltan miles (p.ej. reconciliando contra una copia
        LOCAL desactualizada en vez del QUANTA productivo)."""
        keys = list(missing_keys)
        stmt = text(self.spec.fenix_recover_query).bindparams(
            bindparam(self.spec.fenix_key_param, expanding=True)
        )
        frames = []
        with get_session("FENIX") as session:
            for start in range(0, len(keys), self._RECOVER_BATCH_SIZE):
                batch = keys[start:start + self._RECOVER_BATCH_SIZE]
                df = pd.read_sql(stmt, session.bind, params={self.spec.fenix_key_param: batch})
                if not df.empty:
                    frames.append(df)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        if self.spec.clean_special_chars_cols:
            df = CleanSpecialCharacters(list(self.spec.clean_special_chars_cols)).fit_transform(df)
        df = DropDuplicatesTransform(list(self.spec.conflict_cols)).fit_transform(df)
        return df

    def run(self, db_alias: str = "QUANTA") -> dict:
        """Detecta y recupera las claves faltantes. Retorna un dict serializable a
        XCom: {"keys": [...], "por_fecha": {"YYYY-MM-DD": n}, "watermark": str};
        "keys" vacio si no habia nada que recuperar."""
        empty = {"keys": [], "por_fecha": {}, "watermark": None}
        watermark = self._watermark(db_alias)
        if watermark is None:
            return empty
        empty["watermark"] = str(watermark)

        cutoff = self._cutoff()
        fenix_keys = self._fenix_keys(cutoff, watermark)
        bronze_keys = self._bronze_keys(db_alias, cutoff)
        missing = set(fenix_keys) - bronze_keys
        if not missing:
            return empty

        df = self._recover({fenix_keys[key][0] for key in missing})
        if df.empty:
            return empty

        DWBatchedLoader(
            db_alias=db_alias,
            model_class=self.spec.bronze_entity,
            mode=ModePersistence.UPDATE,
            conflict_cols=self.spec.conflict_cols,
            update_cols=self.spec.update_cols,
            batch_size=2000,
            commit_per_batch=True,
        ).fit_transform(df)

        por_fecha: dict[str, int] = {}
        for key in missing:
            fecha = str(fenix_keys[key][1])[:10]
            por_fecha[fecha] = por_fecha.get(fecha, 0) + 1

        return {
            "keys": sorted(str(key) for key in missing),
            "por_fecha": dict(sorted(por_fecha.items(), reverse=True)),
            "watermark": str(watermark),
        }
