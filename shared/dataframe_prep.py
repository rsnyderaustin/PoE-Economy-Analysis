import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


class DataFramePrep:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 price_col_name: str = None,
                 log_col_name: str = None):
        self._df = dataframe

        self.price_col_name = price_col_name
        self.log_col_name = log_col_name

    def _clone_with_new_df(self, new_df):
        self._df = new_df
        return self

    def __getattr__(self, attr):
        df_attr = getattr(self._df, attr)

        if callable(df_attr):
            def wrapper(*args, **kwargs):
                result = df_attr(*args, **kwargs)
                if isinstance(result, pd.DataFrame):
                    return self._clone_with_new_df(result)
                return result

            return wrapper

        return df_attr

    def __getitem__(self, key):
        return self._df[key]

    def __setitem__(self, key, value):
        self._df[key] = value

    def __repr__(self):
        return repr(self._df)

    @property
    def df(self):
        return self._df

    @df.setter
    def df(self, df):
        self._df = df

    def log_price(self,
                  log_col_name: str):
        self.df[log_col_name] = np.log1p(self.df[self.price_col_name])
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

    def fillna(self, value=0):
        # Fill only on non-categorical columns (exclude object and category types)
        non_cat_cols = self._df.select_dtypes(exclude=['category', 'object']).columns
        self._df[non_cat_cols] = self._df[non_cat_cols].fillna(value)
        return self

    def drop_nan_rows(self):
        f_df = self.features
        f_df = f_df.select_dtypes(['int64', 'float64'])
        valid_indices = f_df[~((f_df == 0) | (pd.isna(f_df))).all(axis=1)].index

        self._df = self._df.loc[valid_indices]

        return self

    def drop_overly_null_columns(self, max_percent_nulls: float):
        null_counts = dict()
        for col in self.features.columns:
            # This most likely happens when rows in the DataFrame are entirely filtered out
            if self._df[col].empty:
                null_counts[col] = float('inf')
                continue

            zero_rows = self._df[col] == 0
            na_rows = pd.isna(self._df[col])
            null_rows = zero_rows | na_rows

            null_counts[col] = null_rows.sum()

        invalid_cols = [col for col in self.features.columns
                        if null_counts[col] / len(self._df) > max_percent_nulls]

        if invalid_cols:
            print(f"Dropping overly-null columns: {invalid_cols}")
        self._df = self._df.drop(columns=invalid_cols)

        return self

    def concat(self, other_df):
        self._df = pd.concat([self._df, other_df], axis=1)
        return self

    def drop_overly_modal_columns(self, max_percent_mode: float):
        mode_counts = dict()
        for col in self.features.columns:
            modes = self._df[col].mode()

            # This most likely happens when rows in the DataFrame are entirely filtered out
            if modes.empty:
                mode_counts[col] = float('inf')
                continue

            mode_value = modes[0]
            mode_counts[col] = (self._df[col] == mode_value).sum()

        invalid_cols = [col for col in self.features.columns
                        if mode_counts[col] / len(self._df) > max_percent_mode]
        if invalid_cols:
            print(f"Dropping overly-modal columns: {invalid_cols}")

        self._df = self._df.drop(columns=invalid_cols)

        return self

    def create_paired_columns(self, column_pairs: list):
        paired_cols = dict()
        for mod1, mod2 in column_pairs:
            paired_cols[(mod1, mod2)] = self._df[mod1] * self._df[mod2]

        for col_name, col in paired_cols.items():
            self._df[col_name] = col

        return self

    def normalize_features(self):
        original_cols = self._df.columns

        # Rename columns if they are tuples
        self._df.columns = [
            f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col
            for col in self._df.columns
        ]

        # Only scale the feature columns (e.g., not the target)
        feature_cols = self.features.columns  # assuming this is a DataFrame
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(self.features)

        # Rebuild just the scaled part as a DataFrame
        scaled_df = pd.DataFrame(scaled_data, columns=feature_cols, index=self._df.index)

        # Replace the original feature columns with scaled values
        self._df = self._df.astype(float)
        self._df.loc[:, feature_cols] = scaled_df

        self._df.columns = original_cols

        return self

    def weight_columns(self, weights: dict):
        for col, weight in weights.items():
            self._df[col] = self._df[col] * weight

        return self

    def multiply_columns(self,
                         columns: list[str],
                         new_col_name: str,
                         replace_source: bool = False):
        self._df[new_col_name] = self._df[columns].prod(axis=1)

        if replace_source:
            self._df = self._df.drop(columns=columns)

        return self
