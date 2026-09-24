from sklearn.base import BaseEstimator, TransformerMixin
from sqlalchemy import text, bindparam
import pandas as pd
from dwh_facturacion.common.session_manager import get_session
import logging
from pathlib import Path


class DatabaseExtractor(BaseEstimator, TransformerMixin):

    def __init__(self, db_alias, query=None, params=None):
        self.query = query
        self.db_alias = db_alias
        self.params = params
        self.log = logging.getLogger(__name__)

    def fit(self, X=None, y=None):
        return self

    def transform(self, X=None):
        if self.query is None:
            raise ValueError("Query must be provided for transformation.")

        try:
            stmt = text(self.query)
            with get_session(self.db_alias) as session:
                df = pd.read_sql(stmt, session.bind, params=self.params)
            return df
        except Exception as e:
            # Importante dejar que la excepción suba: devolver un DataFrame vacío haría
            # que una caída de la fuente se vea como "0 filas nuevas" y la tarea de
            # Airflow termine en éxito sin alertar.
            self.log.error("Error extrayendo de %s: %s", self.db_alias, e.__class__.__name__)
            self.log.error("Mensaje: %s", e)
            raise


class DatabaseExtractorSQLServer(BaseEstimator, TransformerMixin):

    def __init__(self, db_alias, query=None, params=None):
        self.query = query
        self.db_alias = db_alias
        self.params = params
        self.log = logging.getLogger(__name__)

    def fit(self, X=None, y=None):
        return self

    def transform(self, X=None):
        if self.query is None:
            raise ValueError("Query must be provided for transformation.")

        try:
            stmt = text(self.query)

            # Detectar params tipo lista/tupla y marcarlos como "expanding"
            if self.params:
                for key, value in self.params.items():
                    if isinstance(value, (list, tuple, set)):
                        stmt = stmt.bindparams(bindparam(key, expanding=True))

            with get_session(self.db_alias) as session:
                df = pd.read_sql(stmt, session.bind, params=self.params)
            return df
        except Exception as e:
            # Importante dejar que la excepción suba: devolver un DataFrame vacío haría
            # que una caída de la fuente se vea como "0 filas nuevas" y la tarea de
            # Airflow termine en éxito sin alertar.
            self.log.error("Error extrayendo de %s: %s", self.db_alias, e.__class__.__name__)
            self.log.error("Mensaje: %s", e)
            raise


class CsvExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, filepath):
        self.filepath = filepath

    def fit(self, X=None, y=None):
        return self

    def transform(self, X=None):
        if not Path(self.filepath).exists():
            raise FileNotFoundError(f"No se encontró el archivo CSV en: {self.filepath}")

        df = pd.read_csv(self.filepath, dtype=object)

        if df.empty:
            raise ValueError(f"El archivo CSV está vacío: {self.filepath}")

        return df

