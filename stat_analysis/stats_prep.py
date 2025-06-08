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

    @classmethod
    def create_neighborhoods(cls,
                             norm_features_df: pd.DataFrame,
                             raw_features_df: pd.DataFrame,
                             list_prices: pd.Series,
                             neighbors_searched: int = 100
                             ) -> list[Neighborhood]:
        print("Starting determining outliers based on nearest neighbors.")
        norm_features_df = norm_features_df.copy()
        raw_features_df = raw_features_df.copy()

        # RadiusNeighborsRegressor requires that all columns be str
        original_cols = norm_features_df.columns
        norm_features_df.columns = [f"{col[0]}_{col[1]}"
                                    if isinstance(col, tuple) else col for col in norm_features_df.columns]

        print("\nBeginning KNeighborsRegressor analysis.")
        knn = KNeighborsRegressor(n_neighbors=neighbors_searched, n_jobs=-1)
        knn.fit(norm_features_df, list_prices)
        distances, indices = knn.kneighbors(norm_features_df)

        indices = np.array(norm_features_df.index)[indices]

        norm_features_df.columns = original_cols

        print("\nCompiling KNeighborsRegressor results")
        # The first value in each array for distances and indices is the point itself
        distances = [list(arr[1:]) for arr in distances]
        indices = [list(arr[1:]) for arr in indices]

        # Convert to DataFrames so we can reattach indices
        distances_df = pd.DataFrame(distances, index=norm_features_df.index)
        neighbor_indices_df = pd.DataFrame(indices, index=norm_features_df.index)

        print("Creating Neighborhoods.")
        if not norm_features_df.index.equals(raw_features_df.index):
            raise ValueError("Norm features and raw features are misaligned.")

        raw_features_dict = raw_features_df.to_dict(orient="index")
        norm_features_dict = norm_features_df.to_dict(orient="index")
        list_prices_dict = list_prices.to_dict()

        neighborhoods = []
        for i, neighborhood_i in enumerate(norm_features_df.index):
            if i % 1000 == 0:
                print(f"Creating Neighborhood {i} of {len(norm_features_df)}")

            neighbor_idxs = neighbor_indices_df.loc[neighborhood_i]

            new_neighborhood = Neighborhood(
                list_index=neighborhood_i,
                list_data=raw_features_dict[neighborhood_i],
                normalized_list_data=norm_features_dict[neighborhood_i],
                list_price=list_prices_dict[neighborhood_i],
                neighbors_data=[raw_features_dict[i] for i in neighbor_idxs],
                normalized_neighbors_data=[norm_features_dict[i] for i in neighbor_idxs],
                distances=distances_df.loc[neighborhood_i],
                prices=[list_prices_dict[i] for i in neighbor_idxs],
                feature_names=norm_features_df.columns
            )
            neighborhoods.append(new_neighborhood)

        return neighborhoods


class StatsPrep:

    def __init__(self, plot_visuals):
        self._plot_visuals = plot_visuals

        self._original_df = None

    def prep_dataframe(self,
                       df: pd.DataFrame,
                       price_column: str) -> DataFramePrep | None:
        self._original_df = df

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
            .drop_low_information_columns(threshold=0.01,
                                          attribute_pairs_weight=0.5)
        )

        print("Normalizing and weighting features.")
        norm_df_prep = (
            DataFramePrep(df_prep.df.copy(),
                          price_col_name=df_prep.price_col_name,
                          log_col_name=df_prep.log_col_name)
            .normalize_features()
            .weight_columns(df_prep.mutual_info_series)
        )

        neighborhoods = _NearestNeighborAnalysis.create_neighborhoods(
            norm_features_df=norm_df_prep.features,
            raw_features_df=df_prep.features,
            list_prices=norm_df_prep.log_price_column
        )
        # visualize.plot_all_nearest_neighbors(neighborhoods)

        print("Filtering Neighborhoods.")
        for n in neighborhoods:
            n.filter_distant_neighbors(0.1)

        # visualize.plot_number_of_neighbors(neighborhoods)

        print("Determining Neighborhood outliers.")
        outliers_indices = [n.list_index for n in neighborhoods if n.is_outlier(min_neighbors=5)]

        df_prep.drop(index=outliers_indices)
        norm_df_prep.drop(index=outliers_indices)

        # visualize.plot_pca(df_prep.df, df_prep.price_column)
        """for n in neighborhoods:
            for ne in n.neighbors:
                list_data = {col: v for col, v in n.list_data.items() if v != 0}
                ne_data = {col: v for col, v in ne.data.items() if v != 0}
                print(f"\n\n--- New Comparison ---\nDistance:{ne.distance}\nListing:\n{pprint.pformat(list_data)}"
                      f"\nNeighbor:\n{pprint.pformat(ne_data)}")"""

        # visualize.plot_avg_distance_to_nearest_neighbor(norm_features_df)
        # visualize.radar_plot_neighbors(features_df=raw_features_df, indices=indices)
        # visualize.bar_plot_neighbors(neighborhoods)

        return df_prep
