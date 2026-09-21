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
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Type

import pandas as pd
from sqlalchemy import text, bindparam

from dwh_facturacion.common.session_manager import get_session
from dwh_facturacion.etl.extract.db_extractor import DatabaseExtractor
from dwh_facturacion.etl.load.db_load import DWBatchedLoader
from dwh_facturacion.etl.transform.general_functions import CleanSpecialCharacters, DropDuplicatesTransform
from dwh_facturacion.utils.mode_persistence import ModePersistence


@dataclass(frozen=True)
class ReconciliationSpec:
    name: str
    # SELECT <fenix_key_col> ... FROM ... WHERE <ventana> >= :cutoff
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

    def _fenix_keys(self, cutoff: dt.date) -> set:
        df = DatabaseExtractor(
            db_alias="FENIX",
            query=self.spec.fenix_key_set_query,
            params={"cutoff": cutoff},
        ).fit_transform(None)
        if df.empty:
            return set()
        return set(df[self.spec.fenix_key_col].tolist())

    def _bronze_keys(self, db_alias: str, cutoff: dt.date) -> set:
        entity = self.spec.bronze_entity
        key_attr = getattr(entity, self.spec.bronze_key_col)
        window_attr = getattr(entity, self.spec.bronze_window_col)
        with get_session(db_alias) as session:
            rows = session.query(key_attr).filter(window_attr >= cutoff).all()
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

    def run(self, db_alias: str = "QUANTA") -> list[str]:
        """Detecta y recupera las claves faltantes. Retorna la lista de claves
        recuperadas (vacia si no habia nada que recuperar)."""
        cutoff = self._cutoff()
        fenix_keys = self._fenix_keys(cutoff)
        bronze_keys = self._bronze_keys(db_alias, cutoff)
        missing = fenix_keys - bronze_keys
        if not missing:
            return []

        df = self._recover(missing)
        if df.empty:
            return []

        DWBatchedLoader(
            db_alias=db_alias,
            model_class=self.spec.bronze_entity,
            mode=ModePersistence.UPDATE,
            conflict_cols=self.spec.conflict_cols,
            update_cols=self.spec.update_cols,
            batch_size=2000,
            commit_per_batch=True,
        ).fit_transform(df)

        return sorted(str(key) for key in missing)
