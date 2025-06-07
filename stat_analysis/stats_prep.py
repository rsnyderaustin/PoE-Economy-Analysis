import itertools
from sklearn.feature_selection import mutual_info_regression

import numpy as np
import pandas as pd
from sklearn.neighbors import RadiusNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from shared.dataframe_prep import DataFramePrep

from program_logging import LogFile, LogsHandler
from stat_analysis import visualize

stats_log = LogsHandler().fetch_log(LogFile.STATS_PREP)


class _ColumnPairCorrelation:

    def __init__(self, mod1, mod2, correlation, col_series):
        self.mod1 = mod1
        self.mod2 = mod2
        self.correlation = correlation
        self.col_series = col_series


class _CorrelationAnalysis:

    @staticmethod
    def determine_single_column_correlations(df_prep: DataFramePrep) -> dict:
        prices = df_prep.log_price_column
        corrs = df_prep.features.corrwith(prices)
        mod_weights = dict()
        for mod, corr in corrs.items():
            mod_weights[mod] = corr

        return mod_weights

    @staticmethod
    def determine_column_pair_correlations(df_prep: DataFramePrep) -> list[_ColumnPairCorrelation]:
        mod_combinations = list(itertools.combinations(df_prep.features.columns, 2))

        pair_corrs = []
        for mod1, mod2 in mod_combinations:
            pair_df = df_prep.df[[
                df_prep.price_col_name,
                df_prep.log_col_name,
                mod1,
                mod2
            ]]
            pair_df_prep = (DataFramePrep(pair_df,
                                          price_col_name=df_prep.price_col_name,
                                          log_col_name=df_prep.log_col_name)
                            .drop_nan_rows()
                            .multiply_columns(columns=[mod1, mod2], new_col_name=(mod1, mod2), replace_source=True)

                            # Just make sure product isn't all the same value
                            .drop_overly_modal_columns(max_percent_mode=0.99)
                            )

            pair_features = pair_df_prep.features

            if len(pair_features.columns) == 0:
                continue

            if len(pair_features) < 30:
                continue

            pair_corr = pair_features.corrwith(pair_df_prep.log_price_column)
            corr_val = pair_corr[(mod1, mod2)]

            pair_corrs.append(
                _ColumnPairCorrelation(
                    mod1=mod1,
                    mod2=mod2,
                    correlation=corr_val,
                    col_series=pair_features[(mod1, mod2)]
                )
            )
            # print(f"{mod1} and {mod2} correlation -> {corr_val}")

        return pair_corrs


class _NearestNeighborAnalysis:

    @staticmethod
    def _apply_determine_is_outlier(row):
        """
        Determine if the listing's price is an outlier based on weighted neighbor prices.
        Currently not in use.
        """
        list_price = row['list_price']
        prices = pd.Series(row['prices'])
        distances = pd.Series(row['distances'])

        # Compute weights inversely proportional to distance (+ 0.1 to avoid div/0)
        weights = 1 / (distances + 0.1)

        # Sort prices and weights by price
        sorted_indices = prices.argsort()
        sorted_prices = prices.iloc[sorted_indices].values
        sorted_weights = weights.iloc[sorted_indices].values

        # Cumulative weight
        cum_weights = np.cumsum(sorted_weights)
        total_weight = cum_weights[-1]

        # Determine bottom 10% and top 35% weight thresholds
        bottom_weight = total_weight * 0.10
        top_weight = total_weight * 0.35

        # Check if the real price is less than prices before bottom_weight
        lower_idx = np.searchsorted(cum_weights, bottom_weight)
        if list_price < sorted_prices[lower_idx]:
            return True

        # Check if it's more than prices after top_weight
        upper_idx = np.searchsorted(cum_weights, top_weight)
        if list_price > sorted_prices[upper_idx]:
            return True

        return False

    @classmethod
    def filter_out_outliers(cls,
                            norm_features_df: pd.DataFrame,
                            raw_features_df: pd.DataFrame,
                            prices: pd.Series,
                            min_neighbors: int = 5,
                            radius_range: float = 4) -> list:
        norm_features_df = norm_features_df.copy()
        raw_features_df = raw_features_df.copy()

        norm_features_df = norm_features_df.reset_index(drop=True)
        raw_features_df = raw_features_df.reset_index(drop=True)

        norm_features_df.columns = [f"{col[0]}_{col[1]}"
                                    if isinstance(col, tuple) else col for col in norm_features_df.columns]
        features_array = StandardScaler().fit_transform(norm_features_df)
        norm_features_df = pd.DataFrame(features_array, columns=norm_features_df.columns, index=norm_features_df.index)

        radius_neighbors = RadiusNeighborsRegressor(radius=radius_range)
        radius_neighbors.fit(norm_features_df, prices)
        distances, indices = radius_neighbors.radius_neighbors(norm_features_df)

        # visualize.plot_avg_distance_to_nearest_neighbor(norm_features_df)
        # visualize.plot_all_nearest_neighbors(norm_features_df)
        # visualize.radar_plot_neighbors(features_df=raw_features_df, indices=indices)
        # visualize.bar_plot_neighbors(features_df=raw_features_df, indices=indices)

        isolated_indices = [i for i, distances in enumerate(distances) if len(distances) < min_neighbors]

        norm_features_df = norm_features_df.drop(index=isolated_indices)
        raw_features_df = raw_features_df.drop(index=isolated_indices)

        filtered_distances = [d for i, d in enumerate(distances) if i not in isolated_indices]
        filtered_indices = [idx for i, idx in enumerate(indices) if i not in isolated_indices]

        cols_dict = {
            'distances': filtered_distances,
            'prices': [prices.iloc[idx].tolist() for idx in filtered_indices]
        }
        df = pd.DataFrame(cols_dict)

        df['list_price'] = prices

        df['is_price_outlier'] = df.apply(cls._apply_determine_is_outlier, axis=1)
        outlier_indices = df[df['is_price_outlier']].index.tolist()

        all_outliers_indices = isolated_indices + outlier_indices

        return all_outliers_indices


class StatsPrep:

    def __init__(self, plot_visuals):
        self._plot_visuals = plot_visuals

    def prep_dataframe(self, df: pd.DataFrame, price_column: str) -> DataFramePrep | None:
        df_prep = (
            DataFramePrep(df, price_col_name=price_column)
            .drop(columns=['atype'])
            .fillna(0)
            .log_price(log_col_name='log_divs')
            .drop_nan_rows()
            .reset_index(drop=True)
            .drop_overly_null_columns(max_percent_nulls=0.98)
            .drop_overly_modal_columns(max_percent_mode=0.98)
            .drop_duplicates()
        )

        mod_combinations = list(itertools.combinations(df_prep.features.columns, 2))

        pair_cols = {(col1, col2): df_prep.df[col1] * df_prep.df[col2] for col1, col2 in mod_combinations}
        df_prep.concat(pd.DataFrame(pair_cols))

        features_sample = df_prep.features.sample(10000, random_state=42)
        price_sample = df_prep.price_column[features_sample.index]
        mi_scores = mutual_info_regression(features_sample, price_sample, discrete_features='auto')
        mi_series = pd.Series(mi_scores, index=features_sample.columns).sort_values(ascending=False)
        invalid_cols = mi_series[mi_series <= 0.01].index.tolist()
        df_prep.drop(columns=invalid_cols)

        weights = {col: mi for col, mi in mi_series.items() if col not in invalid_cols}

        norm_df_prep = (
            DataFramePrep(df_prep.df.copy(),
                          price_col_name=df_prep.price_col_name,
                          log_col_name=df_prep.log_col_name)
            .normalize_features()
            .weight_columns(weights)
        )

        outlier_indices = _NearestNeighborAnalysis.filter_out_outliers(
            norm_features_df=norm_df_prep.features,
            raw_features_df=df_prep.features,
            prices=norm_df_prep.log_price_column
        )

        df_prep.remove_indices(outlier_indices)

        return df_prep
