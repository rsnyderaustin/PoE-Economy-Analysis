import itertools

import numpy as np
import pandas as pd

from src.market_item_analysis.price_predict_ai_model.stats.model_data_obj import ModelData


class Prepper:

    def __init__(self,
                 dataframe: pd.DataFrame,
                 price_column_name: str,
                 log_price_column_name: str):
        self.data = ModelData(df=dataframe,
                              price_column_name=price_column_name,
                              log_price_column_name=log_price_column_name)

        self.dropped_columns = []

    def create_log_price_column(self, log_price_column_name: str):
        col_name = log_price_column_name
        df = self.data.df

        df[col_name] = np.log1p(df[self.data.price_column_name])
        self.data.log_price_column_name = col_name

        return self

    def fillna(self, value=0):
        # Fill only on non-categorical columns (exclude object and category types)
        non_cat_cols = self._df.select_dtypes(exclude=['category', 'object']).columns
        self._df[non_cat_cols] = self._df[non_cat_cols].fillna(value)
        return self

    def drop_empty_rows(self):
        df = self.data.features_df

        number_columns = df.select_dtypes(include=['int64', 'float64'])
        df = df[number_columns]

        empty_cells_map = df[(df == 0) | (pd.isna(df))]
        empty_rows = empty_cells_map.all(axis=1)
        valid_rows = ~empty_rows

        new_df = df[valid_rows]

        self.data.df = new_df

        return self

    def drop_sparse_columns(self, max_percent_nulls: float):
        df = self.data.features_df

        empty_cells_map = df[(df == 0) | (pd.isna(df))]
        percent_empty = empty_cells_map.mean() * 100
        valid_cols = percent_empty[percent_empty <= max_percent_nulls].index
        invalid_cols = set(df.columns) - set(valid_cols)

        self.data.df = df.drop(columns=list(invalid_cols))

        self.dropped_columns.extend(invalid_cols)

        return self

    def concat(self, other_df):
        self._df = pd.concat([self._df, other_df], axis=1)
        return self

    def drop_modal_columns(self, max_percent_mode: float):
        row_count = self.data.df.shape[0]

        mode_counts = self.data.features_df.apply(lambda col: col.value_counts().max(), axis=0)
        valid_cols = mode_counts[(mode_counts / row_count) <= max_percent_mode].index
        invalid_cols = set(self.data.df.columns) - set(valid_cols)

        self.dropped_columns.extend(invalid_cols)
        self.data.df = self.data.df.drop(columns=list(invalid_cols))

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


class InformationAnalyzer:

    @classmethod
    def determine_mutual_info_regression(cls, metadata: ModelData):




class Stratifier:

    _quantile_tiers = {
        'very_low_price': 0.25,
        'low_price': 0.5,
        'med_price': 0.75,
        'high_price': 0.9,
        'very_high_price': 1.0
    }

    def stratify(self, df: pd.DataFrame, price_column_name: str) -> dict:
        labels = list(self._quantile_tiers.keys())

        tiered = pd.qcut(
            df[price_column_name],
            q=list(self._quantile_tiers.values()),
            labels=labels,
            duplicates="drop"
        )

        return {
            tier: df[tiered == tier]
            for tier in tiered.cat.categories
        }
