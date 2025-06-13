import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor

from . import plots
from program_logging import LogFile, LogsHandler
from shared.dataframe_prep import DataFramePrep
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

    @classmethod
    def prep(cls,
             atype: str,
             df: pd.DataFrame,
             price_column: str) -> dict:
        df['days_since_league_start'] = (df['minutes_since_league_start'] / (60 * 24)).astype(int)

        dfs = DataFramePrep(df, price_col_name=price_column).stratify_dataframe(
            col_name=price_column,
            quantiles=[0.25, 0.5, 0.75, 0.9, 1.0]
        )
        df_tiers = {
            'very_low_price': dfs[0],
            'low_price': dfs[1],
            'med_price': dfs[2],
            'high_price': dfs[3],
            'very_high_price': dfs[4]
        }

        prepped_dfs = dict()
        for tier, df in df_tiers.items():
            print(f"------------ {tier} -----------\n")
            print("Pre-prepping DataFrame.")
            df_prep = (
                DataFramePrep(df, price_col_name=price_column)
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

            plots.plot_binned_median(df=df_prep.df,
                                     col_name='days_since_league_start',
                                     price_col_name='divs',
                                     title=f'{atype.capitalize()} {tier.capitalize()} Median Div Bins',
                                     bin_width=60)

            plots.plot_histogram(df_prep.price_column,
                                 bins=100,
                                 title=f'{atype.capitalize()} {tier.capitalize()} Divs')
            plots.plot_histogram(df_prep.log_price_column,
                                 bins=100,
                                 title=f'{atype.capitalize()} {tier.capitalize()} Log Divs')
            print("Normalizing and weighting features.")
            norm_df_prep = (
                DataFramePrep(df_prep.df.copy(),
                              price_col_name=df_prep.price_col_name,
                              log_col_name=df_prep.log_col_name)
                .normalize_features()
                .weight_columns(df_prep.mutual_info_series)
            )

            neighborhoods = _NeighborhoodFactory.create_neighborhoods(
                norm_features_df=norm_df_prep.features,
                raw_features_df=df_prep.features,
                list_prices=norm_df_prep.log_price_column
            )

            plots.neighbor_distances_histogram(neighborhoods,
                                               title=f'{atype.capitalize()} {tier.capitalize()} Neighbor Distances Histogram')

            print("Filtering Neighborhoods.")
            for n in neighborhoods:
                n.filter_distant_neighbors(distance=0.1)

            plots.number_of_neighbors_histogram(neighborhoods,
                                                title=f'{atype.capitalize()} {tier.capitalize()} Number of Neighbors Histogram')

            print("Determining Neighborhood outliers.")
            outliers_indices = [n.list_index for n in neighborhoods if n.is_outlier(min_neighbors=5)]

            df_prep.drop(index=outliers_indices)
            norm_df_prep.drop(index=outliers_indices)

            plots.plot_binned_median(col_name='max_quality_pdps',
                                     price_col_name=df_prep.price_col_name,
                                     df=df_prep.df,
                                     title=f'{atype.capitalize()} {tier.capitalize()} Pdps Bins')

            plots.plot_pca(df_prep.df,
                           df_prep.price_column,
                           title=f'{atype.capitalize()} {tier.capitalize()} PCA')
            prepped_dfs[tier] = df_prep

        return prepped_dfs
