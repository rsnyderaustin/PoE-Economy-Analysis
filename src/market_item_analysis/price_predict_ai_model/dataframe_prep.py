import itertools

import numpy as np
import pandas as pd


class DataFramePrep:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 price_col_name: str = None,
                 log_col_name: str = None):
        self._df = dataframe

        self._metadata = {
            'price_col_name': price_col_name,
            'log_col_name': log_col_name,
            'mutual_info_series': None
        }

        self.dropped_columns = []

    @property
    def price_col_name(self):
        return self._metadata['price_col_name']

    @price_col_name.setter
    def price_col_name(self, name):
        self._metadata['price_col_name'] = name

    @property
    def log_col_name(self):
        return self._metadata['log_col_name']

    @log_col_name.setter
    def log_col_name(self, name):
        self._metadata['log_col_name'] = name

    @property
    def mutual_info_series(self):
        return self._metadata['mutual_info_series']

    @mutual_info_series.setter
    def mutual_info_series(self, mi_series):
        self._metadata['mutual_info_series'] = mi_series

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

    def print_columns(self):
        print(self.df.columns)
        return self

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

        self.dropped_columns.extend(invalid_cols)

        self._df = self._df.drop(columns=invalid_cols)

        return self

    def concat(self, other_df):
        self._df = pd.concat([self._df, other_df], axis=1)
        return self

    def stratify_dataframe(self, col_name: str, quantiles: list[float]) -> list[pd.DataFrame]:
        quantiles = [self._df[col_name].quantile(q) for q in quantiles]

        first_df = self._df[self._df[col_name] <= quantiles[0]]
        dfs = [first_df]
        for i, quantile in enumerate(quantiles[1:], start=1):
            last_quantile = quantiles[i - 1]
            current_quantile = quantiles[i]
            new_df = self._df[(self._df[col_name] > last_quantile) & (self._df[col_name] <= current_quantile)]
            dfs.append(new_df)

        return dfs

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

        self.dropped_columns.extend(invalid_cols)

        self._df = self._df.drop(columns=invalid_cols)

        return self

    def drop_safe(self, drops: list[str]):
        present_cols = [c for c in drops if c in self._df.columns]
        invalid_cols = [c for c in drops if c not in self._df.columns]

        print(f"{invalid_cols} not in DataFrame. Will not drop.")

        self.dropped_columns.extend(present_cols)

        self._df = self._df.drop(columns=present_cols)
        return self

    def create_paired_columns(self, column_pairs: list):
        paired_cols = dict()
        for mod1, mod2 in column_pairs:
            paired_cols[(mod1, mod2)] = self._df[mod1] * self._df[mod2]

        for col_name, col in paired_cols.items():
            self._df[col_name] = col

        return self

    def normalize_features(self):
        from sklearn.preprocessing import StandardScaler

        original_cols = self._df.columns

        # Rename columns if they are tuples
        self._df.columns = [
            f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col
            for col in self._df.columns
        ]

        # Only scale the non-categorical feature columns
        feature_cols = [col for col in self.features.columns
                        if np.issubdtype(self.features[col].dtype, np.number)]
        scalable_features = self.features[feature_cols]

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(scalable_features)

        # Rebuild just the scaled part as a DataFrame
        scaled_df = pd.DataFrame(scaled_data, columns=feature_cols, index=self._df.index)
        scaled_df = scaled_df.astype(float)

        self._df[scaled_df.columns] = scaled_df
        self._df.columns = original_cols

        return self

    def weight_columns(self, weights: dict):
        for col, weight in weights.items():
            if col not in self._df.columns:
                continue

            print(f"Weighting {col}: {weight}")
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

    def pair_features(self):
        mod_combinations = list(itertools.combinations(self.features.columns, 2))
        pair_cols = {(col1, col2): self.df[col1] * self.df[col2] for col1, col2 in mod_combinations}
        self.concat(pd.DataFrame(pair_cols))
        return self

    def drop_low_information_columns(self, threshold: float):
        from sklearn.feature_selection import mutual_info_regression

        features_sample = self.features.sample(n=min(len(self.features), 10000), random_state=42)
        price_sample = self.price_column[features_sample.index]
        mi_scores = mutual_info_regression(features_sample, price_sample, discrete_features='auto')
        mi_series = pd.Series(mi_scores, index=features_sample.columns).sort_values(ascending=False)

        invalid_cols = mi_series[mi_series < threshold].index.tolist()

        self.dropped_columns.extend(invalid_cols)

        if not invalid_cols:
            self.mutual_info_series = mi_series
            print(f"No low information columns found. Returning.")
            return self

        print(f"Dropping low information columns: {invalid_cols}")
        self.drop(columns=invalid_cols)

        mi_series = mi_series.drop(columns=invalid_cols)
        self.mutual_info_series = mi_series

        return self
