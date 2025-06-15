import copy

import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor

from . import plots
from .utils import ModelLifeCycle
from program_logging import LogFile, LogsHandler
from price_predict_ai_model.dataframe_prep import DataFramePrep
from price_predict_ai_model.neighborhood_class import Neighborhood

stats_log = LogsHandler().fetch_log(LogFile.STATS_PREP)


class _NeighborhoodFactory:

    @staticmethod
    def create_neighborhoods(norm_features_df: pd.DataFrame,
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

        print("Creating neighborhoods.")
        neighborhoods = []
        for i, neighborhood_i in enumerate(norm_features_df.index):
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
        print(f"Created {len(neighborhoods)} neighborhoods.")

        return neighborhoods


class StatsPrep:

    @staticmethod
    def _normalize_data(df_prep: DataFramePrep) -> DataFramePrep:
        norm_df_prep = (
            DataFramePrep(df_prep.df,
                          price_col_name=df_prep.price_col_name,
                          log_col_name=df_prep.log_col_name)
            .normalize_features()
            .weight_columns(df_prep.mutual_info_series)
        )

        return norm_df_prep

    @staticmethod
    def _initial_data_prep(df: pd.DataFrame,
                           price_column: str):
        df_prep = (
            DataFramePrep(df,
                          price_col_name=price_column)
            .drop_duplicates()
            .drop(columns=['atype', 'minutes_since_league_start'])
            .fillna(0)
            .log_price(log_col_name='log_divs')
            .drop_nan_rows()
            .reset_index(drop=True)
            .drop_overly_null_columns(max_percent_nulls=0.98)
            .drop_overly_modal_columns(max_percent_mode=0.98)
            # Drop the local modifiers - they are accounted for in dps calculations
            .drop_safe(
                ['mod_adds_n_to_n_cold_damage',
                 'mod_adds_n_to_n_fire_damage',
                 'mod_adds_n_to_n_lightning_damage',
                 'mod_adds_n_to_n_chaos_damage',
                 'mod_adds_n_to_n_physical_damage']
            )
            .drop_low_information_columns(threshold=0.01)
        )
        return df_prep

    @classmethod
    def prep(cls,
             model_lifecycle: ModelLifeCycle,
             df: pd.DataFrame,
             price_column: str,
             neighbor_distance_threshold: float = 0.1) -> DataFramePrep:

        atype = model_lifecycle.atype
        tier = model_lifecycle.tier

        print(f"------------ {tier} -----------\n")
        print("Pre-prepping DataFrame.")
        df_prep = cls._initial_data_prep(df=df,
                                         price_column=price_column)

        model_lifecycle.dropped_columns = df_prep.dropped_columns
        model_lifecycle.mi_series = df_prep.mutual_info_series

        print("Normalizing and weighting features.")
        norm_df_prep = cls._normalize_data(copy.deepcopy(df_prep))

        print("Creating neighborhoods.")
        neighborhoods = _NeighborhoodFactory.create_neighborhoods(
            norm_features_df=norm_df_prep.features,
            raw_features_df=df_prep.features,
            list_prices=norm_df_prep.log_price_column
        )
        print("Filtering Neighborhoods.")
        for n in neighborhoods:
            n.filter_distant_neighbors(distance=neighbor_distance_threshold)

        print("Determining Neighborhood outliers.")
        outliers_indices = [n.list_index for n in neighborhoods if n.is_outlier(min_neighbors=5)]

        df_prep.drop(index=outliers_indices)
        norm_df_prep.drop(index=outliers_indices)

        # Code below is just plotting
        plots.binned_median(df=df_prep.df,
                            col_name='days_since_league_start',
                            price_col_name='divs',
                            title=f'{atype.capitalize()} {tier.capitalize()} Median Div Bins')

        plots.histogram(df_prep.price_column,
                        bins=100,
                        title=f'{atype.capitalize()} {tier.capitalize()} Divs')
        plots.histogram(df_prep.log_price_column,
                        bins=100,
                        title=f'{atype.capitalize()} {tier.capitalize()} Log Divs')

        plots.neighbor_distances_histogram(neighborhoods,
                                           title=f'{atype.capitalize()} {tier.capitalize()} Neighbor Distances Histogram')

        plots.number_of_neighbors_histogram(neighborhoods,
                                            title=f'{atype.capitalize()} {tier.capitalize()} Number of Neighbors Histogram')

        plots.binned_median(col_name='max_quality_pdps',
                            price_col_name=df_prep.price_col_name,
                            df=df_prep.df,
                            title=f'{atype.capitalize()} {tier.capitalize()} Pdps Bins',
                            bin_width=60)

        plots.plot_pca(df_prep.df,
                       df_prep.price_column,
                       title=f'{atype.capitalize()} {tier.capitalize()} PCA')

        return df_prep

