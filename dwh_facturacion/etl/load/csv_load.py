import re

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from unidecode import unidecode


class CsvLoad(BaseEstimator, TransformerMixin):
    def __init__(
            self,
            path_csv: str,
            sep: str = ','
    ):
        self.path_csv = path_csv
        self.sep = sep

    def fit(self, X, y=None):
        return self

    def transform(self, X=None):
        X = pd.read_csv(self.path_csv, dtype=object, sep=self.sep)
        return X
