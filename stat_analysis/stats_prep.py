import itertools

import numpy as np
import pandas as pd
from sklearn.neighbors import RadiusNeighborsRegressor
from sklearn.preprocessing import StandardScaler
from shared.dataframe_prep import DataFramePrep

from program_logging import LogFile, LogsHandler

stats_log = LogsHandler().fetch_log(LogFile.STATS_PREP)


class _CorrelationAnalysis:

    @staticmethod
    def determine_single_column_weights(df_prep: DataFramePrep,
                                        correlation_threshold: float,
                                        weight_multiplier: float = None) -> dict:
        features_df = df_prep.fetch_features()
        prices = df_prep.fetch_log_price_column()
        corrs = features_df.corrwith(prices)
        mod_weights = dict()
        for mod, corr in corrs.items():
            if corr >= correlation_threshold:
                mod_weights[mod] = corr

        if weight_multiplier:
            mod_weights = {mod: weight * weight_multiplier for mod, weight in mod_weights.items()}

        return mod_weights

    @staticmethod
    def determine_column_pair_weights(df_prep: DataFramePrep,
                                      correlation_threshold: float) -> dict:
        mod_combinations = list(itertools.combinations(df_prep.df.columns, 2))

        # Build initial dictionary of DataFrames filtered by nonzero rows
        valid_pairs_weights = dict()
        for mod1, mod2 in mod_combinations:
            pair_df = df_prep.fetch_columns_df([df_prep.log_col_name, mod1, mod2])
            pair_df_prep = (DataFramePrep(pair_df,
                                          price_col_name=df_prep.log_col_name)
                            .drop_nan_rows()
                            .multiply_columns(columns=[mod1, mod2])
                            .drop([mod1, mod2], inplace=True)
                            .drop_overly_modal_columns(max_percent_mode=0.97)
                            )

            pair_df = pair_df_prep.fetch_features()

            # The DataFrame is empty in the rare case that the product is overly-modal
            if pair_df.empty:
                continue

            if len(pair_df) < 30:
                continue

            pair_corr = pair_df.corrwith(pair_df_prep.log_price_column)
            corr_val = pair_corr[(mod1, mod2)]

            if corr_val >= correlation_threshold:
                stats_log.info(f"Valid column correlation {(mod1, mod2)}: {corr_val}")
                valid_pairs_weights[(mod1, mod2)] = corr_val

        return valid_pairs_weights


class _NearestNeighborAnalysis:

    @staticmethod
    def _apply_determine_is_outlier(row):
        """
        Determine if the listing's price is an outlier based on weighted neighbor prices.
        Currently not in use.
        """
        list_price = row['real_price']
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
    def determine_outliers(cls,
                           features_df: pd.DataFrame,
                           prices: pd.Series,
                           min_neighbors: int = 20,
                           radius_range: float = 0.5) -> list:
        radius_neighbors = RadiusNeighborsRegressor(radius=radius_range)
        radius_neighbors.fit(features_df, prices)
        distances, indices = radius_neighbors.radius_neighbors(features_df)

        isolated_indices = [i for i, distances in enumerate(distances) if len(distances) < min_neighbors]

        cols_dict = {
            'distances': distances.tolist(),
            'prices': [prices.iloc[idx].tolist() for idx in indices]
        }
        df = pd.DataFrame(cols_dict)

        df['real_price'] = prices

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
            .fillna(0)
            .select_dtypes(['int64', 'float64'])
            .log_price(log_column_name='log_divs')
            .drop_nan_rows()
            .reset_index(drop=True)
            .drop_overly_null_columns(max_percent_nulls=0.97)
            .drop_overly_modal_columns(max_percent_mode=0.97)
        )
        features_df = df_prep.fetch_features()

        single_column_weights = _CorrelationAnalysis.determine_single_column_weights(
            df_prep=df_prep,
            correlation_threshold=0.4,
            weight_multiplier=2.5
        )

        column_pair_weights = _CorrelationAnalysis.determine_column_pair_weights(
            df_prep=df_prep,
            correlation_threshold=0.4
        )

        if not single_column_weights and not column_pair_weights:
            return

        column_pairs = list(column_pair_weights.keys())
        single_columns = list(single_column_weights.keys())

        if column_pairs:
            df_prep.create_paired_columns(column_pairs)

        (df_prep
         .normalize_features()
         .apply_column_weights(weights={**single_column_weights, **column_pair_weights})
         )

        outlier_indices = _NearestNeighborAnalysis.determine_outliers(
            features_df=df_prep.fetch_features(),
            prices=df_prep.log_price_column
        )

        df_prep.remove_indices(outlier_indices)

        return df_prep
