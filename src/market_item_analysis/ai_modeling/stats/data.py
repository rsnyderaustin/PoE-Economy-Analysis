import itertools
from copy import deepcopy
from dataclasses import dataclass
from enum import auto, Enum

import numpy as np
import pandas as pd

from src.market_item_analysis.ai_modeling.listing_lifecycle import ListingLifecycle
from src.market_item_analysis.ai_modeling.config.listing_schema import ListingColumn


class ColumnCategory(Enum):
    TARGET = auto()
    FEATURE = auto()
    NUMERICAL = auto()
    CATEGORICAL = auto()

@dataclass
class QuantileTier:
    name: str
    quantile: float

class ListingModelData:

    def __init__(self,
                 df: pd.DataFrame,
                 lifecycle: ListingLifecycle,
                 quantile_tier: QuantileTier | None = None):
        self.df = df
        self.lifecycle = lifecycle

        self.quantile_tier = quantile_tier

        self._price_logged = False

    def __getattr__(self, name):
        """
        If we don't have the attribute 'name',
        try to find it in our internal DataFrame.
        """
        # Look up the attribute in the self.df object
        attr = getattr(self.df, name)

        # If it's a method (like .head(), .fillna(), .groupby()),
        # return a wrapper so it stays "bound" to the DataFrame
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                # If the result is a DataFrame, wrap it back in ModelData
                if isinstance(result, pd.DataFrame):
                    return ListingModelData(result)
                return result

            return wrapper

        # If it's a property (like .columns, .index), just return it
        return attr

    def __deepcopy__(self, memo) -> "ListingModelData":
        self.lifecycle.
        return ListingModelData(
            df=deepcopy(self.df, memo),
            lifecycle=self.lifecycle,
            quantile_tier=self._quantile_tier
        )

    @property
    def row_count(self) -> int:
        return self.df.shape[0]

    @property
    def price_col(self):
        return self.df[ListingColumn.PRICE.value]

    def create_log_target_col(self):
        self.df[ListingColumn.LOG_PRICE.value] = np.log1p(self.price_col)

        self._price_logged = True

        return self

    def _target_cols(self):
        cols = [ListingColumn.PRICE.value]
        if self._price_logged:
            cols.append(ListingColumn.LOG_PRICE.value)

        return cols

    def _feature_cols(self) -> list[str]:
        return [col for col in self.df.columns if col not in {ListingColumn.PRICE.value, ListingColumn.LOG_PRICE.value}]

    def _categorical_cols(self) -> list[str]:
        return self.df.select_dtypes(include=['category', 'object']).columns

    def _numerical_cols(self) -> list[str]:
        return self.df.select_dtypes(include=['int64', 'float64']).columns

    _COLUMN_CATEGORY_MAP = {
        ColumnCategory.TARGET: _target_cols,
        ColumnCategory.FEATURE: _feature_cols,
        ColumnCategory.NUMERICAL: _numerical_cols,
        ColumnCategory.CATEGORICAL: _categorical_cols
    }
    def filter_by_categories(self, col_categories: list[ColumnCategory]):
        df = self.df.copy()
        for category in col_categories:
            cols = self._COLUMN_CATEGORY_MAP[category]()
            df = df[cols]
        return df

    def fill_na(self, col_categories: list[ColumnCategory], value=0):
        df = self.filter_by_categories(col_categories)
        df = df.fillna(value)
        self.df.update(df)
        return self

    def drop_empty_rows(self, col_categories: list[ColumnCategory]):
        df = self.filter_by_categories(col_categories)

        empty_cells_map = df[(df == 0) | (pd.isna(df))]
        empty_rows = empty_cells_map.all(axis=1)
        valid_rows = ~empty_rows

        self.df = self.df[valid_rows]

        return self

    def drop_null_columns(self, col_categories: list[ColumnCategory], max_percent_nulls: float):
        df = self.filter_by_categories(col_categories=col_categories)

        empty_cells_map = df[(df == 0) | (pd.isna(df))]
        percent_empty = empty_cells_map.mean() * 100
        valid_cols = percent_empty[percent_empty <= max_percent_nulls].index
        invalid_cols = set(df.columns) - set(valid_cols)

        self.df = self.df.drop(columns=list(invalid_cols))

        self._dropped_cols.extend(invalid_cols)

        return self
    
    def concat(self, df: pd.DataFrame):
        self.df = pd.concat([self.df, df], axis=1)
        return self
    
    def drop_modal_columns(self, col_categories: list[ColumnCategory], max_percent_mode: float):
        df = self.filter_by_categories(col_categories=col_categories)

        mode_counts = df.apply(lambda col: col.value_counts().max(), axis=0)
        invalid_cols = mode_counts[(mode_counts / self.row_count) > max_percent_mode].index

        self.df = self.df.drop(columns=invalid_cols)
        self._dropped_cols.extend(invalid_cols)

        return self

    def normalize(self, col_categories: list[ColumnCategory]):
        from sklearn.preprocessing import StandardScaler

        df = self.filter_by_categories(col_categories=col_categories)
        feature_cols = [col for col in df.columns if np.issubdtype(df[col].dtype, np.number)]

        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(df)

        # Rebuild just the scaled part as a DataFrame
        scaled_df = pd.DataFrame(scaled_data, columns=feature_cols, index=df.index)
        scaled_df = scaled_df.astype(float)

        df[scaled_df.columns] = scaled_df
        self.df.update(scaled_df)

        return self

    def weight_columns(self, weights: dict[str, float]):
        for col, weight in weights.items():
            self.df[col] = self.df[col] * weight

        return self

    def multiply_columns(self,
                         columns: list[str],
                         new_col_name: str,
                         drop_columns: bool = False):
        self.df[new_col_name] = self.df[columns].prod(axis=1)

        if drop_columns:
            self.df = self.df.drop(columns=columns)

        return self

    def pair_cols(self, col_categories: list[ColumnCategory]):
        df = self.filter_by_categories(col_categories=col_categories)
        col_combos = list(itertools.combinations(df.columns, 2))
        pair_cols = {f"paired_{col1}_{col2}": self.df[col1] * self.df[col2] for col1, col2 in col_combos}
        self.concat(pd.DataFrame(pair_cols))

        return self

    def drop_low_information_columns(self,
                                     col_categories: list[ColumnCategory],
                                     drop_threshold: float,
                                     analysis_sample_count: int = 10000):
        from sklearn.feature_selection import mutual_info_regression

        df = self.filter_by_categories(col_categories=col_categories)
        sample = df.sample(n=min(len(df), analysis_sample_count), random_state=42)

        target_sample = self.target_col[sample.index]

        mi_scores = mutual_info_regression(sample, target_sample, discrete_features='auto')
        mi_series = pd.Series(mi_scores, index=sample.columns).sort_values(ascending=False)

        invalid_cols = mi_series[mi_series < drop_threshold].index.tolist()

        self.df = self.df.drop(columns=invalid_cols)

        return self

    def stratify(self, quantile_tiers: list[QuantileTier]) -> list["ListingModelData"]:
        labels = [quantile_tier.name for quantile_tier in quantile_tiers]
        quantiles = [quantile_tier.quantile for quantile_tier in quantile_tiers]

        tiered = pd.qcut(
            self.target_col,
            q=quantiles,
            labels=labels,
            duplicates="drop"
        )

        for tier_name in tiered.cat.categories:
            df = self.df[tiered == tier_name]
            quantile_tier = [quantile_tier for quantile_tier in quantile_tiers
                             if quantile_tier.name == tier_name][0]
            model_data = deepcopy(self)
            quantile_tier.df = df

        return quantile_tiers
