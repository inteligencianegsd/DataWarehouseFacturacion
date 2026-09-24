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
    # True: ademas de recuperar faltantes, borra de Bronze las claves de la ventana que
    # ya no existen en Fenix (asientos eliminados en el origen). Solo contabilidad.
    sync_deletes: bool = False


class ReconciliationPipeline:
    # Si una corrida detecta mas borrados que esto, falla sin borrar nada: es mas
    # probable un problema de lectura en Fenix que una eliminacion masiva real.
    MAX_DELETES = 500

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

    def _bronze_window_values(self, db_alias: str, keys: set) -> dict:
        """clave -> valor de la columna de ventana en Bronze (para agrupar por fecha)."""
        entity = self.spec.bronze_entity
        key_attr = getattr(entity, self.spec.bronze_key_col)
        window_attr = getattr(entity, self.spec.bronze_window_col)
        out, keys = {}, list(keys)
        with get_session(db_alias) as session:
            for start in range(0, len(keys), self._RECOVER_BATCH_SIZE):
                batch = keys[start:start + self._RECOVER_BATCH_SIZE]
                out.update(session.query(key_attr, window_attr).filter(key_attr.in_(batch)).all())
        return out

    def _deleted_in_fenix(self, candidates: set) -> set:
        """De las claves que estan en Bronze pero no en el set de la ventana de Fenix,
        devuelve solo las que de verdad ya no existen en Fenix (se busca por clave, sin
        ventana: si solo cambio la fecha contable, la fila sigue existiendo)."""
        still_there = self._recover(candidates)
        if still_there.empty:
            return set(candidates)
        return set(candidates) - set(still_there[self.spec.fenix_key_col].tolist())

    def _delete_from_bronze(self, db_alias: str, keys: set) -> None:
        entity = self.spec.bronze_entity
        key_attr = getattr(entity, self.spec.bronze_key_col)
        keys = list(keys)
        with get_session(db_alias) as session:
            for start in range(0, len(keys), self._RECOVER_BATCH_SIZE):
                batch = keys[start:start + self._RECOVER_BATCH_SIZE]
                session.query(entity).filter(key_attr.in_(batch)).delete(synchronize_session=False)

    @staticmethod
    def _count_by_date(fechas) -> dict:
        por_fecha: dict[str, int] = {}
        for fecha in fechas:
            fecha = str(fecha)[:10]
            por_fecha[fecha] = por_fecha.get(fecha, 0) + 1
        return dict(sorted(por_fecha.items(), reverse=True))

    def run(self, db_alias: str = "QUANTA") -> dict:
        """Detecta y recupera las claves faltantes (y, si spec.sync_deletes, borra de
        Bronze las eliminadas en Fenix). Retorna un dict serializable a XCom:
        {"keys": [...], "por_fecha": {...}, "watermark": str,
         "deleted": [...], "deleted_por_fecha": {...}}."""
        result = {"keys": [], "por_fecha": {}, "watermark": None,
                  "deleted": [], "deleted_por_fecha": {}}
        watermark = self._watermark(db_alias)
        if watermark is None:
            return result
        result["watermark"] = str(watermark)

        cutoff = self._cutoff()
        fenix_keys = self._fenix_keys(cutoff, watermark)
        bronze_keys = self._bronze_keys(db_alias, cutoff)

        missing = set(fenix_keys) - bronze_keys
        if missing:
            df = self._recover({fenix_keys[key][0] for key in missing})
            if not df.empty:
                DWBatchedLoader(
                    db_alias=db_alias,
                    model_class=self.spec.bronze_entity,
                    mode=ModePersistence.UPDATE,
                    conflict_cols=self.spec.conflict_cols,
                    update_cols=self.spec.update_cols,
                    batch_size=2000,
                    commit_per_batch=True,
                ).fit_transform(df)
                result["keys"] = sorted(str(key) for key in missing)
                result["por_fecha"] = self._count_by_date(fenix_keys[key][1] for key in missing)

        if self.spec.sync_deletes:
            candidates = bronze_keys - set(fenix_keys)
            deleted = self._deleted_in_fenix(candidates) if candidates else set()
            if len(deleted) > self.MAX_DELETES:
                raise RuntimeError(
                    f"Backfill {self.spec.name}: {len(deleted)} claves de Bronze no existen en "
                    f"Fenix (tope {self.MAX_DELETES}). No se borro nada; revisar antes."
                )
            if deleted:
                fechas = self._bronze_window_values(db_alias, deleted)
                self._delete_from_bronze(db_alias, deleted)
                result["deleted"] = sorted(str(key) for key in deleted)
                result["deleted_por_fecha"] = self._count_by_date(fechas.values())

        return result
