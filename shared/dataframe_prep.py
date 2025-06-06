import numpy as np
import pandas as pd


class StandardScaler:
    pass


class DataFramePrep:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 price_col_name: str = None):
        self._df = dataframe

        self.price_col_name = price_col_name
        self.log_col_name = None

    def __getattr__(self, attr):
        # Delegate all missing attributes to the internal DataFrame
        return getattr(self._df, attr)

    def __getitem__(self, key):
        return self._df[key]

    def __setitem__(self, key, value):
        self._df[key] = value

    def __repr__(self):
        return repr(self._df)

    @property
    def df(self):
        return self._df

    def log_price(self,
                  price_col_name: str,
                  log_col_name: str):
        self.df[log_col_name] = np.log1p(self.df[price_col_name])
        self.log_col_name = log_col_name
        return self

    @property
    def price_column(self) -> pd.Series:
        return self.df[self.price_col_name]

    @property
    def log_price_column(self) -> pd.Series:
        return self.df[self.log_col_name]

    @property
    def features(self) -> pd.DataFrame:
        target_cols = [col for col in [self.price_col_name, self.log_col_name] if col is not None]
        feature_cols = [col for col in self._df.columns if col not in target_cols]

        return self._df[feature_cols]

    def fetch_columns_df(self, columns: list[str]) -> pd.DataFrame:
        return self._df[columns]

    def drop_nan_rows(self):
        features_df = self.fetch_features()

        valid_indices = features_df[~((features_df == 0) | (pd.isna(features_df))).all(axis=1)].index

        self._df = self._df.loc[valid_indices]

        return self

    def drop_overly_null_columns(self, max_percent_nulls: float):
        null_counts = dict()
        for col in self._df.columns:
            zero_rows = self._df[col] == 0
            na_rows = pd.isna(self._df[col])
            null_rows = zero_rows | na_rows

            null_counts[col] = null_rows.sum()

        valid_cols = [col for col, nulls_count in null_counts.items()
                      if nulls_count / len(self._df) < max_percent_nulls]
        self._df = self._df[valid_cols]

        return self

    def drop_overly_modal_columns(self, max_percent_mode: float):
        mode_counts = dict()
        for col in self._df.columns:
            mode_value = self._df[col].mode()[0]
            mode_counts[col] = (self._df[col] == mode_value).sum()

        valid_cols = [col for col, mode_count in mode_counts.items()
                      if mode_count / len(self._df) < max_percent_mode]
        self._df = self._df[valid_cols]

        return self

    def create_paired_columns(self, column_pairs: list):
        paired_cols = dict()
        for mod1, mod2 in column_pairs:
            paired_cols[f"{mod1}_{mod2}"] = self._df[mod1] * self._df[mod2]

        for col_name, col in paired_cols.items():
            self._df[col_name] = col

        return self

    def normalize_features(self):
        features_df = self.fetch_features()
        original_cols = features_df.columns

        scaler = StandardScaler()
        new_data = scaler.fit_transform(features_df)
        new_df = pd.DataFrame(new_data)
        new_df.columns = original_cols

        self._df = new_df

        return self

    def apply_column_weights(self, weights: dict):
        for col, weight in weights.items():
            self._df[col] = self._df[col] * weight

        return self

    def remove_indices(self, indices):
        self._df = self._df.iloc[indices]

        return self

    def multiply_columns(self,
                         columns: list[str],
                         inplace=True):
        col_name = tuple(columns)

        if not inplace:
            return self._df[columns].prod(axis=1)

        self._df[col_name] = self._df[columns].prod(axis=1)
        return self
