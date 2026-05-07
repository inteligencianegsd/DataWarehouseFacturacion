import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
import logging

from sqlalchemy import update, bindparam, func

from dwh_facturacion.common.session_manager import get_session
from dwh_facturacion.utils.mode_persistence import ModePersistence


class DWLoader(BaseEstimator, TransformerMixin):
    def __init__(
            self,
            db_alias,
            model_class,
            conflict_cols=None,
            update_cols=None,
            mode:ModePersistence = ModePersistence.INSERT
    ):
        """
        Carga los datos al datawarehouse (Postgres SQL por defecto).
        - table_name: nombre de la tabla destino
        - if_exists:
        - index: si incluye índice del DataFrame en la tabla
        """
        self.model_class = model_class
        self.db_alias = db_alias
        self.conflict_cols = conflict_cols
        self.mode = mode
        self.update_cols = update_cols
        self.logger = logging.getLogger("database logger")

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("El input de DWLoader debe ser un DataFrame de pandas.")

        try:
            # El Bulk de Update Date no es capaz de reconocer Valores NaT, np.nan mapea ese valor y lo transformers a
            # None que es Similar a Null. El pd.notnull no tuvo esa capacidad, dejaba el NaT de igual manera.
            X.replace({np.nan: None}, inplace=True)
            with get_session(db_alias=self.db_alias) as session:
                self.model_class.persist_from_dataframe(session, X, self.conflict_cols, self.mode, self.update_cols)
            self.logger.info(f"{len(X)} filas cargadas a la tabla '{self.model_class.__table__.name}'.")
            # print(f"[INFO] {len(X)} filas cargadas a la tabla '{self.model_class.__table__.name}'.")
        except Exception as e:
            self.logger.error("Error en inserción SQLAlchemy: %s", e.__class__.__name__)
            self.logger.error("Mensaje: %s", e)
            raise
        print('Finalizo Proceso de Carga al DataWarehouse')
        return X


class DWBatchedLoader(BaseEstimator, TransformerMixin):
    def __init__(
            self,
            db_alias,
            model_class,
            conflict_cols=None,
            mode: ModePersistence = ModePersistence.INSERT,
            update_cols=None,
            batch_size: int = 10_000,
            commit_per_batch: bool = True,
    ):
        """
        Carga los datos al Data Warehouse en batches.

        Parámetros:
        - db_alias: alias de la base de datos (para get_session)
        - model_class: clase de SQLAlchemy que expone persist_from_dataframe(session, df, conflict_cols, mode, update_cols)
        - conflict_cols: columnas de conflicto para ON CONFLICT
        - mode: modo de operación ('INSERT', 'UPSERT', etc. según maneje tu persist_from_dataframe)
        - update_cols: columnas a actualizar en caso de conflicto (para UPSERT, etc.)
        - batch_size: tamaño de cada batch (número de filas del DataFrame)
        - commit_per_batch: si True, hace commit después de cada batch
        """
        self.model_class = model_class
        self.db_alias = db_alias
        self.conflict_cols = conflict_cols
        self.mode = mode
        self.update_cols = update_cols
        self.batch_size = batch_size
        self.commit_per_batch = commit_per_batch
        self.logger = logging.getLogger("database logger")

    def fit(self, X, y=None):
        return self

    def _iter_batches(self, X: pd.DataFrame):
        """
        Generador de batches del DataFrame.
        """
        n_rows = len(X)
        for start in range(0, n_rows, self.batch_size):
            end = start + self.batch_size
            yield start, end, X.iloc[start:end]

    def transform(self, X: pd.DataFrame):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("El input de DWBatchedLoader debe ser un DataFrame de pandas.")

        if X.empty:
            self.logger.info("DataFrame vacío recibido en DWBatchedLoader. No se realiza ninguna carga.")
            print("No hay filas para cargar al DataWarehouse.")
            return X

        try:
            # Mismo tratamiento de NaN / NaT que eb DWLoader original
            X.replace({np.nan: None}, inplace=True)

            total_rows = len(X)
            total_batches = (total_rows + self.batch_size - 1) // self.batch_size
            self.logger.info(
                "Iniciando carga en batches. Total filas: %s, batch_size: %s, total_batches: %s. Se cargara info en la Base: %s",
                total_rows,
                self.batch_size,
                total_batches,
                self.db_alias,
            )

            with get_session(db_alias=self.db_alias) as session:
                for i, (start, end, batch_df) in enumerate(self._iter_batches(X), start=1):
                    try:
                        self.model_class.persist_from_dataframe(
                            session,
                            batch_df,
                            self.conflict_cols,
                            self.mode,
                            self.update_cols,
                        )
                        if self.commit_per_batch:
                            session.commit()

                        msg = (
                            f"[INFO] Batch {i}/{total_batches}: "
                            f"{len(batch_df)} filas cargadas "
                            f"a la tabla '{self.model_class.__table__.name}' "
                            f"(filas {start}–{end - 1})."
                        )
                        self.logger.info(msg)
                    except Exception as e_batch:
                        # Si un batch falla, logueamos el contexto del batch
                        self.logger.error(
                            "Error en inserción del batch %s/%s. Rango de filas: %s-%s. Error: %s - %s",
                            i,
                            total_batches,
                            start,
                            end - 1,
                            e_batch.__class__.__name__,
                            e_batch,
                        )
                        # Importante dejar que la excepción suba para que el pipeline falle de forma explícita
                        raise

        except Exception as e:
            self.logger.error("Error en inserción SQLAlchemy (proceso por batches): %s", e.__class__.__name__)
            self.logger.error("Mensaje: %s", e)
            raise
        return X


class DWBatchedUpdater:
    def __init__(self, db_alias, model_class, batch_size: int = 10_000, update_date_col: str = "update_date"):
        """
        Carga los datos al datawarehouse usando UPDATE puro en batches.

        - db_alias: alias de la base de datos
        - model_class: clase SQLAlchemy de la tabla destino
        - batch_size: tamaño de batch
        """
        self.model_class = model_class
        self.db_alias = db_alias
        self.batch_size = batch_size
        self.update_date_col = update_date_col
        self.logger = logging.getLogger("database logger")

    def fit(self, X, y=None):
        return self

    def _iter_batches(self, X: pd.DataFrame):
        n_rows = len(X)
        for start in range(0, n_rows, self.batch_size):
            end = start + self.batch_size
            yield start, end, X.iloc[start:end]

    def transform(self, X: pd.DataFrame):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("El input de DWBatchedLoader debe ser un DataFrame de pandas.")

        if X.empty:
            self.logger.info("DataFrame vacío recibido. No se realiza ninguna carga.")
            print("No hay filas para actualizar en el DataWarehouse.")
            return X

        try:
            # Convertir NaN/NaT a None para SQLAlchemy
            X.replace({np.nan: None}, inplace=True)

            total_rows = len(X)
            total_batches = (total_rows + self.batch_size - 1) // self.batch_size
            self.logger.info(
                "Iniciando actualización en batches. Total filas: %s, batch_size: %s, total_batches: %s",
                total_rows,
                self.batch_size,
                total_batches,
            )

            with get_session(db_alias=self.db_alias) as session:
                for i, (start, end, batch_df) in enumerate(self._iter_batches(X), start=1):
                    try:
                        # Crear el diccionario de valores dinámicamente
                        values_dict = {
                            self.update_date_col: bindparam("fecha_caducidad"),  # columna dinámica recibe bindparam
                            "fecha_emision": bindparam("fecha_emision"),
                            "update_date": func.now()  # si quieres que esta siempre sea ahora
                        }

                        stmt = (
                            update(self.model_class.__table__)
                            .where(self.model_class.__table__.c.serial_firma == bindparam("b_serial_firma"))
                            .values(**values_dict)
                        )

                        batch_df['b_serial_firma'] = batch_df['serial_firma']
                        session.execute(stmt, batch_df.to_dict("records"))
                        session.commit()

                        msg = (
                            f"[INFO] Batch {i}/{total_batches}: "
                            f"{len(batch_df)} filas actualizadas "
                            f"en '{self.model_class.__table__.name}' "
                            f"(filas {start}-{end - 1})."
                        )
                        self.logger.info(msg)

                    except Exception as e_batch:
                        self.logger.error(
                            "Error en batch %s/%s, filas %s-%s: %s - %s",
                            i,
                            total_batches,
                            start,
                            end - 1,
                            e_batch.__class__.__name__,
                            e_batch
                        )
                        raise

        except Exception as e:
            self.logger.error("Error en actualización SQLAlchemy: %s", e.__class__.__name__)
            self.logger.error("Mensaje: %s", e)
            raise
        return X
