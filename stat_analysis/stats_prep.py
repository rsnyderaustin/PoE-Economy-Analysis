import itertools
import pprint

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.neighbors import KNeighborsRegressor

from program_logging import LogFile, LogsHandler
from shared.dataframe_prep import DataFramePrep
from stat_analysis import visualize
from .neighborhood_class import Neighborhood

stats_log = LogsHandler().fetch_log(LogFile.STATS_PREP)


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

    @staticmethod
    def _filter_self_neighbor(features_df, distances, indices):
        filtered_dists = []
        filtered_indices = []

        for dist_list, idx_list, i in zip(distances, indices, range(len(features_df))):
            filtered = [(d, idx) for d, idx in zip(dist_list, idx_list) if idx != i]
            if filtered:
                dists, idxs = zip(*filtered)
                filtered_dists.append(list(dists))
                filtered_indices.append(list(idxs))
            else:
                filtered_dists.append([])
                filtered_indices.append([])

        return filtered_dists, filtered_indices

    @classmethod
    def determine_outliers(cls,
                           norm_features_df: pd.DataFrame,
                           raw_features_df: pd.DataFrame,
                           list_prices: pd.Series,
                           min_neighbors: int = 10,
                           neighbors_searched: int = 100,
                           within_range: float = 0.1
                           ) -> list[Neighborhood]:
        print("Starting determining outliers based on nearest neighbors.")
        norm_features_df = norm_features_df.copy()
        raw_features_df = raw_features_df.copy()

        # RadiusNeighborsRegressor naturally resets the index, so this allows us to convert the index back
        index_convert = {i: idx for i, idx in enumerate(raw_features_df.index)}

        # RadiusNeighborsRegressor requires that all columns be str
        original_cols = norm_features_df.columns
        norm_features_df.columns = [f"{col[0]}_{col[1]}"
                                    if isinstance(col, tuple) else col for col in norm_features_df.columns]

        print("\nBeginning KNeighborsRegressor analysis.")
        knn = KNeighborsRegressor(n_neighbors=neighbors_searched, n_jobs=-1)
        knn.fit(norm_features_df, list_prices)
        distances, indices = knn.kneighbors(norm_features_df)

        norm_features_df.columns = original_cols

        print("\nCompiling KNeighborsRegressor results")
        # The first value in each array for distances and indices is the point itself
        distances = [list(arr[1:]) for arr in distances]
        indices = [list(arr[1:]) for arr in indices]

        print("Creating neighborhoods.")
        raw_arr = raw_features_df.to_numpy()
        norm_arr = norm_features_df.to_numpy()
        prices_arr = np.array(list_prices)

        # Make a map from label index to position if needed
        idx_map = {k: v for v, k in enumerate(norm_features_df.index)}

        neighborhoods = [
            Neighborhood(
                main_point=raw_arr[idx_map[index_convert[neighborhood_i]]],
                normalized_main_point=norm_arr[idx_map[index_convert[neighborhood_i]]],
                neighbors_data=[
                    raw_arr[idx_map[index_convert[i]]] for i in indices[neighborhood_i]
                ],
                normalized_neighbors_data=[
                    norm_arr[idx_map[index_convert[i]]] for i in indices[neighborhood_i]
                ],
                distances=distances[neighborhood_i],
                prices=[prices_arr[idx_map[index_convert[i]]] for i in indices[neighborhood_i]],
                feature_names=norm_features_df.columns
            )
            for neighborhood_i in range(len(norm_features_df))
        ]

        return neighborhoods

        visualize.plot_all_nearest_neighbors(neighborhoods)

        print("Filtering neighborhoods.")
        for n in neighborhoods:
            n.filter_distant_neighbors(within_range)
        neighborhoods = [n for n in neighborhoods if len(n.neighbors) >= min_neighbors]

        # visualize.plot_avg_distance_to_nearest_neighbor(norm_features_df)
        # visualize.radar_plot_neighbors(features_df=raw_features_df, indices=indices)
        visualize.bar_plot_neighbors(neighborhoods)

        # Filter out any items that don't have all their closest neighbors within the 'radius_range'
        isolated_indices = [i for i, ds in enumerate(distances) if ds[-1] > within_range]

        index_ = []
        cols_dict = {
            'distances': [],
            'prices': [],
            'list_price': []
        }
        for row_i, (n_distances, n_indices) in enumerate(zip(distances, indices)):
            if row_i in isolated_indices:
                continue

            index_.append(index_convert[row_i])

            list_price = list_prices.loc[index_convert[row_i]]
            cols_dict['list_price'].append(list_price)

            cols_dict['distances'].append(n_distances)

            converted_indices = [index_convert[i] for i in n_indices]
            n_prices = [list_prices.loc[i] for i in converted_indices]
            cols_dict['prices'].append(n_prices)

        df = pd.DataFrame(cols_dict, index=index_)

        print("Determining outliers based on neighbors pricing.")
        df['is_price_outlier'] = df.apply(cls._apply_determine_is_outlier, axis=1)
        outlier_indices = df[df['is_price_outlier']].index.tolist()

        all_outliers_indices = set(isolated_indices) | set(outlier_indices)

        return all_outliers_indices


class StatsPrep:

    def __init__(self, plot_visuals):
        self._plot_visuals = plot_visuals

        self._original_df = None

    def prep_dataframe(self,
                       df: pd.DataFrame,
                       price_column: str,
                       mutual_info_threshold: float = 0.05) -> DataFramePrep | None:
        print("Pre-prepping DataFrame.")
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
            .pair_features()
            .drop_low_information_columns(mutual_info_threshold)
        )

        self._original_df = df_prep.df

        print("Normalizing and weighting features.")
        norm_df_prep = (
            DataFramePrep(df_prep.df.copy(),
                          price_col_name=df_prep.price_col_name,
                          log_col_name=df_prep.log_col_name)
            .normalize_features()
            .weight_columns(df_prep.mutual_info_series)
        )

        outlier_indices = _NearestNeighborAnalysis.determine_outliers(
            original_df=self._original_df,
            norm_features_df=norm_df_prep.features,
            raw_features_df=df_prep.features,
            list_prices=norm_df_prep.log_price_column
        )

        df_prep.drop(index=outlier_indices)

        return df_prep
