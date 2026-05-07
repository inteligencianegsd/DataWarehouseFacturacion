import re
from typing import List

from pandas import DataFrame
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
from unidecode import unidecode


class RenameColumnsTransform(BaseEstimator, TransformerMixin):
    def __init__(self, dict_names):
        self.dict_names = dict_names

    def fit(self, X, y=None):
        # No fitting neccesary for this transformes
        return self

    def transform(self, X=pd.DataFrame()):
        X.rename(columns=self.dict_names, inplace=True)
        return X


class DropDuplicatesTransform(BaseEstimator, TransformerMixin):
    def __init__(self, subset, keep='first', reset_index=True, drop_index=True):
        self.subset = subset
        self.keep = keep
        self.reset_index = reset_index
        self.drop_index = drop_index

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame):
        mask = X[self.subset].isnull().all(axis=1)
        X = X[~mask]
        X.drop_duplicates(subset=self.subset, keep=self.keep, inplace=True)
        if self.reset_index:
            X.reset_index(drop=self.drop_index, inplace=True)
        return X


class UpperLetterTransform(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame):
        for column in self.columns:
            if column in X.columns:
                X[column] = X[column].str.upper()
        return X


class AddConstantColumn(BaseEstimator, TransformerMixin):
    def __init__(self, column_name: str, value):
        self.column_name = column_name
        self.value = value

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame):
        X[self.column_name] = self.value
        return X


class ReplaceTextTransform(BaseEstimator, TransformerMixin):
    def __init__(self, old_value, new_value, column):
        self.old_value = old_value
        self.new_value = new_value
        self.column = column

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame):
        X[self.column] = X[self.column].replace(self.old_value, self.new_value)
        return X


class TrimRowsObject(BaseEstimator, TransformerMixin):
    def __init__(self, columns=None):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame):
        if self.columns is None:
            self.columns = [column for column in X.select_dtypes(include=['object', 'string'])]
        for column in self.columns:
            X[column] = X[column].str.strip()
        return X


class SortValues(BaseEstimator, TransformerMixin):
    def __init__(self, columns, order_ascending=True):
        self.columns = columns
        self.order_ascending = order_ascending

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame):
        X.sort_values(by=self.columns, ascending=self.order_ascending, inplace=True)
        # 🔥 Resetear el índice para que quede ordenado desde 0
        X.reset_index(drop=True, inplace=True)
        return X


class DropColumns(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame()):
        X.drop(columns=self.columns, inplace=True)
        return X


class FilterColumns(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X=pd.DataFrame()):
        X = X[self.columns]
        return X


class DropRowNaDates(BaseEstimator, TransformerMixin):
    def __init__(self, columns):
        """
        columns: lista de columnas de tipo fecha en las cuales se eliminarán filas con valores nulos.
        """
        self.columns = columns

    def fit(self, X, y=None):
        # No necesita aprender nada de los datos
        return self

    def transform(self, X):
        """
        Elimina filas donde cualquiera de las columnas de fecha especificadas tenga valores nulos.
        """
        X = X.copy()
        X = X.dropna(subset=self.columns)
        return X


class ConcatDataFrames(BaseEstimator, TransformerMixin):
    def __init__(self, ignore_index=True):
        self.ignore_index = ignore_index

    def fit(self, X, y=None):
        return self

    def transform(self, X_list):
        """
        Espera una lista o iterable de DataFrames y los concatena por filas.
        """
        if not isinstance(X_list, (list, tuple)):
            raise ValueError("El argumento X_list debe ser una lista o tupla de DataFrames.")

        return pd.concat(X_list, axis=0, ignore_index=self.ignore_index)


class CheckValueFlag(BaseEstimator, TransformerMixin):
    def __init__(
            self,
            column_name_to_check: str,
            target_value,
            flag_column: str = "flag"
    ):
        self.column_name_to_check = column_name_to_check
        self.target_value = target_value
        self.flag_column = flag_column

    def fit(self, X, y=None):
        return self

    def transform(self, X: DataFrame = None):
        X[self.flag_column] = X[self.column_name_to_check] == self.target_value
        return X


class CheckValueNotEqualFlag(BaseEstimator, TransformerMixin):
    def __init__(
            self,
            column_name_to_check: str,
            target_value,
            flag_column: str = "flag"
    ):
        self.column_name_to_check = column_name_to_check
        self.target_value = target_value
        self.flag_column = flag_column

    def fit(self, X, y=None):
        return self

    def transform(self, X: DataFrame = None):
        X[self.flag_column] = X[self.column_name_to_check] != self.target_value
        return X


class CleanSpecialCharacters(BaseEstimator, TransformerMixin):
    def __init__(
            self,
            columns: List[str]
    ):
        self.columns = columns

    def fit(self, X, y=None):
        return self

    def transform(self, X:DataFrame = None):
        cols_to_fix = X.columns.intersection(self.columns)
        for column in cols_to_fix:
            X[column] = X[column].apply(
                lambda x: re.sub(r'[\x00-\x1F\x7F]', '', unidecode(str(x))) if pd.notnull(x) else x
            )
        return X


