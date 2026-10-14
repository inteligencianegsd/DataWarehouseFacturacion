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

Si la spec define bronze_row_hash_expr (contabilidad), ademas de claves se comparan
valores: el fenix_key_set_query trae un `row_hash` y Bronze calcula el mismo hash; las
claves presentes en ambos lados con hash distinto se re-traen de Fenix y se hace upsert
("updated"). Las filas que salieron de la ventana en Fenix pero siguen existiendo (p.ej.
se cambio su fecha contable a antes del cutoff) tambien se actualizan en vez de quedar
con la fecha vieja en Bronze.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Type

import pandas as pd
from sqlalchemy import text, bindparam, or_, literal_column

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
    # Expresion SQL (Postgres) sobre la tabla Bronze que reproduce el `row_hash` del
    # fenix_key_set_query. Si esta definida, se comparan valores ademas de claves.
    bronze_row_hash_expr: str | None = None
    # True: la ventana arranca el 1 de enero del ano fiscal abierto (ver
    # ReconciliationPipeline.FISCAL_CLOSE_GRACE_DAYS) si eso es anterior a lookback_days.
    fiscal_year_window: bool = False


class ReconciliationPipeline:
    # Si una corrida detecta mas borrados que esto, falla sin borrar nada: es mas
    # probable un problema de lectura en Fenix que una eliminacion masiva real.
    MAX_DELETES = 500
    # Dias despues del 1 de enero en que el ano anterior se sigue revisando: contabilidad
    # hace ajustes de cierre del ano fiscal anterior hasta ~abril.
    FISCAL_CLOSE_GRACE_DAYS = 120

    def __init__(self, spec: ReconciliationSpec, lookback_days: int = 30):
        self.spec = spec
        self.lookback_days = lookback_days

    def _cutoff(self) -> dt.date:
        today = dt.date.today()
        cutoff = today - dt.timedelta(days=self.lookback_days)
        if self.spec.fiscal_year_window:
            fiscal_year = (today - dt.timedelta(days=self.FISCAL_CLOSE_GRACE_DAYS)).year
            cutoff = min(cutoff, dt.date(fiscal_year, 1, 1))
        return cutoff

    @property
    def _compare_values(self) -> bool:
        return self.spec.bronze_row_hash_expr is not None

    def _watermark(self, db_alias: str):
        """Watermark actual del incremental de esta tabla en Bronze (None si vacia)."""
        with get_session(db_alias) as session:
            return self.spec.bronze_entity.get_last_transaction_date(session)

    def _fenix_keys(self, cutoff: dt.date, watermark) -> pd.DataFrame:
        """Claves de Fenix en la ventana, hasta el watermark. DataFrame indexado por la
        clave normalizada (como queda en Bronze) con columnas `orig` (clave cruda en
        Fenix), `fecha_ref` y, si se comparan valores, `row_hash`. Es un DataFrame y no
        un dict porque en contabilidad la ventana es el ano fiscal (millones de filas)."""
        df = DatabaseExtractor(
            db_alias="FENIX",
            query=self.spec.fenix_key_set_query,
            params={"cutoff": cutoff, "watermark": watermark},
        ).fit_transform(None)
        cols = ["orig", "fecha_ref"] + (["row_hash"] if self._compare_values else [])
        if df.empty:
            return pd.DataFrame(columns=cols)
        key_col = self.spec.fenix_key_col
        df["orig"] = df[key_col]
        if key_col in self.spec.clean_special_chars_cols:
            df = CleanSpecialCharacters([key_col]).fit_transform(df)
        if self._compare_values:
            df["row_hash"] = df["row_hash"].astype("int64")
        df = df.drop_duplicates(subset=[key_col], keep="last").set_index(key_col)
        return df[cols]

    def _bronze_keys(self, db_alias: str, cutoff: dt.date) -> pd.DataFrame:
        """Claves de Bronze en la ventana: DataFrame indexado por clave, con `row_hash`
        si se comparan valores."""
        entity = self.spec.bronze_entity
        key_attr = getattr(entity, self.spec.bronze_key_col)
        window_attr = getattr(entity, self.spec.bronze_window_col)
        cols = [key_attr]
        if self._compare_values:
            cols.append(literal_column(self.spec.bronze_row_hash_expr).label("row_hash"))
        with get_session(db_alias) as session:
            # Incluye las filas con la columna de ventana en NULL, igual que el lado Fenix
            # (clientes/vendedores con fecha_act NULL), para no reportarlas cada noche.
            rows = session.query(*cols).filter(
                or_(window_attr >= cutoff, window_attr.is_(None))
            ).all()
        names = ["key"] + (["row_hash"] if self._compare_values else [])
        return pd.DataFrame(rows, columns=names).set_index("key")

    @staticmethod
    def _changed_keys(fenix: pd.DataFrame, bronze: pd.DataFrame) -> pd.Index:
        """Claves presentes en ambos lados cuyo row_hash difiere."""
        both = fenix[["row_hash"]].join(bronze[["row_hash"]], how="inner", rsuffix="_bronze")
        return both.index[both["row_hash"] != both["row_hash_bronze"].astype("int64")]

    def _upsert(self, db_alias: str, df: pd.DataFrame) -> None:
        DWBatchedLoader(
            db_alias=db_alias,
            model_class=self.spec.bronze_entity,
            mode=ModePersistence.UPDATE,
            conflict_cols=self.spec.conflict_cols,
            update_cols=self.spec.update_cols,
            batch_size=2000,
            commit_per_batch=True,
        ).fit_transform(df)

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

    def _deleted_in_fenix(self, candidates: set) -> tuple[set, pd.DataFrame]:
        """De las claves que estan en Bronze pero no en el set de la ventana de Fenix,
        separa las que de verdad ya no existen en Fenix (se busca por clave, sin ventana:
        si solo cambio la fecha contable, la fila sigue existiendo) de las que siguen
        ahi. Retorna (claves borradas, filas completas de Fenix de las que siguen)."""
        still_there = self._recover(candidates)
        if still_there.empty:
            return set(candidates), still_there
        return set(candidates) - set(still_there[self.spec.fenix_key_col].tolist()), still_there

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
        Bronze las eliminadas en Fenix; si spec.bronze_row_hash_expr, actualiza las que
        cambiaron de valor). Retorna un dict serializable a XCom:
        {"keys": [...], "por_fecha": {...}, "watermark": str,
         "updated": [...], "updated_por_fecha": {...},
         "deleted": [...], "deleted_por_fecha": {...}}."""
        result = {"keys": [], "por_fecha": {}, "watermark": None,
                  "updated": [], "updated_por_fecha": {},
                  "deleted": [], "deleted_por_fecha": {}}
        watermark = self._watermark(db_alias)
        if watermark is None:
            return result
        result["watermark"] = str(watermark)

        cutoff = self._cutoff()
        fenix_keys = self._fenix_keys(cutoff, watermark)
        bronze_keys = self._bronze_keys(db_alias, cutoff)

        missing = fenix_keys.index.difference(bronze_keys.index)
        changed = self._changed_keys(fenix_keys, bronze_keys) if self._compare_values else pd.Index([])
        to_upsert = missing.union(changed)
        if len(to_upsert):
            # .tolist(): tipos nativos de Python, pymysql/psycopg2 no adaptan numpy.int64
            df = self._recover(set(fenix_keys.loc[to_upsert, "orig"].tolist()))
            if not df.empty:
                self._upsert(db_alias, df)
                result["keys"] = sorted(str(key) for key in missing)
                result["por_fecha"] = self._count_by_date(fenix_keys.loc[missing, "fecha_ref"])
                result["updated"] = sorted(str(key) for key in changed)
                result["updated_por_fecha"] = self._count_by_date(fenix_keys.loc[changed, "fecha_ref"])

        if self.spec.sync_deletes:
            candidates = set(bronze_keys.index.difference(fenix_keys.index).tolist())
            deleted, moved = self._deleted_in_fenix(candidates) if candidates else (set(), pd.DataFrame())
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
            # Siguen en Fenix pero salieron de la ventana (cambio su fecha contable a antes
            # del cutoff): se actualizan para que Bronze no se quede con la fecha vieja.
            if self._compare_values and not moved.empty:
                self._upsert(db_alias, moved)
                moved_keys = moved[self.spec.fenix_key_col].tolist()
                result["updated"] = sorted(result["updated"] + [str(key) for key in moved_keys])
                result["updated_por_fecha"] = self._count_by_date(
                    list(fenix_keys.loc[changed, "fecha_ref"]) + list(moved[self.spec.bronze_window_col])
                )

        return result
