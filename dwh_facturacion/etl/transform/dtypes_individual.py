import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class DtypeDateTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert date columns in a DataFrame to datetime format.
    """

    def __init__(self, column, date_format='%Y-%m-%d %H:%M:%S'):
        self.date_format = date_format
        self.column = column

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        X[self.column] = pd.to_datetime(X[self.column], errors='coerce', format=self.date_format)
        # COnversion para el problema del TIpo de Dato NAT Documentar

        return X


class DtypeCategoricalTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to categorical type.
    """

    def __init__(self, column):
        self.column = column

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")
        X[self.column] = X[self.column].astype('category')

        return X


class DtypeFloatTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to float type.
    """

    def __init__(self, column):
        self.column = column

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")
        X[self.column] = X[self.column].astype(float)

        return X


class DtypeIntegerTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to integer type.
    """

    def __init__(self, column, dtype_int='int64'):
        self.column = column
        self.dtype_int = dtype_int

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")
        X[self.column] = X[self.column].astype(dtype=self.dtype_int)

        return X


class DtypeStringTransform(BaseEstimator, TransformerMixin):
    """
    Transformer to convert specified columns in a DataFrame to string type.
    """

    def __init__(self, column):
        self.column = column

    def fit(self, X, y=None):
        # No fitting necessary for this transformer
        return self

    def transform(self, X):
        if not isinstance(X, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame.")

        X[self.column] = X[self.column].astype(str)

        return X
