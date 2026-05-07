import re

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from unidecode import unidecode


class DtypeStringNormalization(BaseEstimator, TransformerMixin):
    """
    Transformer to clean and normalize string columns while preserving NULL values.

    - Convierte valores a string
    - Corta al tamaño deseado
    - Normaliza acentos (á→a, ñ→n, etc.)
    - Elimina caracteres especiales
    - Convierte espacios múltiples
    - Devuelve pd.NA para valores vacíos o nulos
    """

    def __init__(self, columns, length=255):
        self.columns = columns if isinstance(columns, list) else [columns]
        self.length = length

    def fit(self, X, y=None):
        return self

    def _clean_text(self, value):
        """Normalize text but return pd.NA for null/empty results."""

        # Casos nulos desde el inicio
        if value is None or pd.isna(value):
            return pd.NA

        # Convertir a string y limpiar espacios
        value = str(value).strip()

        # Si está vacío después del strip → NULL
        if value == "":
            return pd.NA

        # Normalizar acentos y caracteres unicode (ñ→n, á→a, etc.)
        value = unidecode(value)

        # Convertir a mayúsculas
        value = value.upper()

        # Quitartodo lo que no sea A-Z, 0-9 o espacio
        value = re.sub(r"[^A-Z0-9 ]", "", value)

        # Reemplazar múltiples espacios por uno solo
        value = re.sub(r"\s+", " ", value).strip()

        # Si queda vacío → NULL
        if value == "":
            return pd.NA

        return value

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        for col in self.columns:
            if col in X.columns:
                X[col] = (
                    X[col]
                    .apply(lambda v: v if pd.isna(v) else str(v))  # No convertir NA en "nan"
                    .str[:self.length]
                    .apply(self._clean_text)
                )

        return X


class DtypeDateTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert date columns in a DataFrame to datetime format.
    """

    def __init__(self, columns, date_format='%Y-%m-%d %H:%M:%S'):
        self.date_format = date_format
        self.columns = columns if isinstance(columns, list) else [columns]

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        for col in self.columns:
            X[col] = pd.to_datetime(X[col], errors='coerce', format=self.date_format)
            # Handle conversion errors by coercing invalid parsing to NaT

        return X


class DtypeCategoricalTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to categorical type.
    """

    def __init__(self, columns):
        self.columns = columns if isinstance(columns, list) else [columns]

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        for col in self.columns:
            X[col] = X[col].astype('category')

        return X


class DtypeFloatTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to float type.
    """

    def __init__(self, columns):
        self.columns = columns if isinstance(columns, list) else [columns]

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")
        for col in self.columns:
            X[col] = X[col].astype(float)

        return X


class DtypeIntegerTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to integer type.
    """

    def __init__(self, columns, dtype_int='Int64'):
        self.columns = columns if isinstance(columns, list) else [columns]
        self.dtype_int = dtype_int

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):

        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")
        for col in self.columns:
            if col in X.columns:
                X[col] = X[col].astype(dtype=self.dtype_int)

        return X


class DtypeStringTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to string type.
    """

    def __init__(self, columns, length=255):
        self.columns = columns if isinstance(columns, list) else [columns]
        self.length = length

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        for col in self.columns:
            if col in X.columns:
                # Guardar máscara de nulos
                mask_null = X[col].isna()

                # Convertir a string SOLO los no nulos
                X.loc[~mask_null, col] = (
                    X.loc[~mask_null, col]
                    .astype(str)
                    .str.upper()
                    .str[:self.length]
                )

                # Restaurar nulos como pd.NA
                X.loc[mask_null, col] = pd.NA

        return X


class DtypeBooleanTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to string type.
    """

    def __init__(self, columns):
        self.columns = columns if isinstance(columns, list) else [columns]

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        for col in self.columns:
            if col in X.columns:
                X[col] = X[col].astype(bool)

        return X
