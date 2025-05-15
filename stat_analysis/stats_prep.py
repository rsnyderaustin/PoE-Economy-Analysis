import logging
import itertools

from dataclasses import dataclass
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.neighbors import RadiusNeighborsRegressor
from sklearn.preprocessing import StandardScaler

from . import utils


class DataFrameParts:

    def __init__(self, df: pd.DataFrame, price_column: str):
        self.df = df
        self.prices = df[price_column]
        self.features = df.drop(columns=[price_column])


@dataclass
class CorrelationResults:
    transformed_features: pd.DataFrame
    single_weights: dict
    pair_weights: dict


class CorrelationAnalyzer:

    @staticmethod
    def _determine_suitable_single_columns(features, prices, correlation_threshold: float) -> dict:
        corrs = features.corrwith(prices)
        mod_weights = dict()
        for mod, corr in corrs.items():
            if corr >= correlation_threshold:
                mod_weights[mod] = corr

        return mod_weights

    @staticmethod
    def _determine_suitable_pair_columns(features: pd.DataFrame, prices, correlation_threshold: float) -> dict:
        mod_combinations = list(itertools.combinations(features.columns, 2))

        # Step 1: Build initial dictionary of DataFrames filtered by nonzero indices
        filtered_dfs = {
            (mod1, mod2): utils.get_nonzero_dataframe(features, [mod1, mod2])
            for mod1, mod2 in mod_combinations
        }

        # Step 2: Filter out DataFrames with fewer than 30 samples
        pair_dfs = {pair: pair_df for pair, pair_df in filtered_dfs.items() if len(pair_df) >= 30}

        # Step 3: Determine how each mod pair correlates with the price of the item
        valid_pairs_weights = dict()
        for (mod1, mod2), pair_df in pair_dfs.items():
            # Create a dataframe with a single column that is the product of mod columns
            product_df = pd.DataFrame({(mod1, mod2): pair_df[mod1] * pair_df[mod2]})

            pair_corr = product_df.corrwith(prices)
            corr_val = pair_corr[(mod1, mod2)]
            if corr_val >= correlation_threshold:
                logging.info(f"{(mod1, mod2)} correlation: {corr_val}")
                valid_pairs_weights[(mod1, mod2)] = corr_val

        return valid_pairs_weights

    @classmethod
    def transform_columns_by_correlation(cls,
                                         df_parts: DataFrameParts,
                                         single_correlation_threshold: float,
                                         pair_correlation_threshold: float) -> CorrelationResults:
        single_weights = cls._determine_suitable_single_columns(features=df_parts.features,
                                                                prices=df_parts.prices,
                                                                correlation_threshold=single_correlation_threshold)
        pair_weights = cls._determine_suitable_pair_columns(features=df_parts.features,
                                                            prices=df_parts.prices,
                                                            correlation_threshold=pair_correlation_threshold)
        df_setup = {col: df_parts.features[col] for col in single_weights.keys()}
        for mod1, mod2 in pair_weights.keys():
            df_setup[utils.normalize_column_name((mod1, mod2))] = df_parts.features[mod1] * df_parts.features[mod2]

        features = pd.DataFrame(df_setup)
        return CorrelationResults(transformed_features=features,
                                  single_weights=single_weights,
                                  pair_weights=pair_weights)


class StatsPrep:

    def __init__(self, df: pd.DataFrame, atype: str, price_column: str):
        self.df_parts = DataFrameParts(df=df,
                                       price_column=price_column)
        self.atype = atype


    def plot_correlations(self, df: pd.DataFrame):
        df = df.drop(columns=['exalts'], errors='ignore')
        corr = df.corr()
        plt.figure(figsize=(8, 6))
        plt.title(f'{self.atype}')
        sns.heatmap(corr, annot=True, cmap='coolwarm')
        plt.show()

    @staticmethod
    def plot_dimensions(self, df: pd.DataFrame):
        for col in df.columns:
            if col == 'exalts':
                continue

            plt.figure(figsize=(8, 6))
            plt.title(f'{self.atype}_{col}')
            sns.scatterplot(x=df[col], y=df['exalts'])
            plt.show()

    def plot_pca(self, df: pd.DataFrame):
        if self.price_column in df.columns:
            price = df['exalts']

        pca = PCA(n_components=2)
        reduced_data = pca.fit_transform(df.drop(columns=['exalts']))
        pca_df = pd.DataFrame(reduced_data, columns=['pca1', 'pca2'])
        pca_df['exalts'] = price

        # Plot the clusters
        plt.figure(figsize=(10, 7))
        c_palette = sns.color_palette("flare", as_cmap=True)
        # plot_df.loc[plot_df['cluster'] == -1, 'cluster'] = 999
        sns.scatterplot(data=pca_df, x='pca1', y='pca2', hue='exalts', palette=c_palette, edgecolor='black')

        # Customize the plot
        plt.title("Clusters of Mod Combinations (Excluding Price) Based on PCA Components")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.legend(title='exalts')
        plt.show()

    def _visualize_radius_neighbors_regression(self, df, features, distances, indices, price_column):
        data = {
            'index': [],
            'distance': [],
            'neighbor_price': [],
            'listing_price': [],
            **{f"mainpoint_{f}": [] for f in features.columns},
            **{f: [] for f in features.columns}
        }
        # Display the neighbors
        inputs = list(zip(distances, indices))
        for main_i, (dx_to_ns, idxs) in enumerate(inputs):
            # Get the features of the main point
            main_point_features = features.iloc[main_i].values
            # Loop through each index and corresponding distance
            for dx, idx in zip(dx_to_ns, idxs):
                if dx == main_i:  # Skip this neighbor if its ourself
                    continue

                data['index'].append(main_i)
                data['listing_price'].append(df[price_column].iloc[main_i])
                data['neighbor_price'].append(df[price_column].iloc[idx])
                for i, col in enumerate(features.columns):
                    data[f"mainpoint_{col}"].append(main_point_features[i])

                data['distance'].append(dx)
                neighbor_features = features.iloc[idx]

                for col, val in neighbor_features.items():
                    data[col].append(val)

            if i >= 250:
                break

        neighbors_df = pd.DataFrame(data)

    def _filter_insignificant_columns(self,
                                      variance_threshold: float = 0.05,
                                      non_mode_count_threshold: int = 30,
                                      correlation_threshold: float = 0.3) -> pd.DataFrame:

        df = self.df_parts.features.select_dtypes(['int64', 'float64'])
        valid_cols = df.columns[((df != 0) & ~(pd.isna(df))).any()]
        df = df[valid_cols]

        # Filter out columns that have less than 30 values that are not the mode value
        valid_cols = []
        for col in df.columns:
            mode_val = df[col].mode()[0]
            s = df[col] != mode_val
            non_mode_count = s.sum()
            if non_mode_count < non_mode_count_threshold:
                continue

            non_mode_percent = non_mode_count / len(df)
            if non_mode_percent >= variance_threshold:  # If there's enough non-mode values then this column is okay
                valid_cols.append(col)
                continue

            variance_df = df[df[col] != mode_val]
            corr_val = variance_df.corrwith(self.df_parts.prices)
            if corr_val >= correlation_threshold:
                valid_cols.append(col)
                continue

        return df[valid_cols]

    def _filter_out_outliers(self,
                             features_df,
                             radius: float = 0.2,
                             price_column='exalts',
                             min_neighbors: int = 3,
                             threshold=0.25):
        features = self.df_parts.features

        regressor = RadiusNeighborsRegressor(radius=radius, weights='distance')
        regressor.fit(features, self.prices)
        dxs, indices = regressor.radius_neighbors(features)

        # The first value for dxs and indices is the point itself. We only want neighbors
        indices = [subarray[1:] for subarray in indices]
        prices = [
            [self.prices.iloc[index] for index in subarray]
            for subarray in indices
        ]

        neighbor_indices = [i for i, subarray in enumerate(prices) if len(subarray) >= min_neighbors]
        isolated_indices = [i for i, subarray in enumerate(prices) if len(subarray) < min_neighbors]
        standalones_df = features.iloc[isolated_indices]
        neighbors_df = features.iloc[neighbor_indices]

        neighbors_df.reset_index(drop=True)
        sorted_prices = [np.sort(subarray) for subarray in prices if len(subarray) >= min_neighbors]
        bottom_3_prices = [
            np.median(subarray[:3])
            for subarray in sorted_prices
        ]
        # medians = [np.median(subarray) for subarray in prices if len(subarray) >= min_neighbors]
        neighbors_df['neighbors_exalts'] = bottom_3_prices

        # Calculate price deviation
        neighbors_df['price_deviation'] = np.abs(neighbors_df[price_column] - neighbors_df['neighbors_exalts']) / \
                                          neighbors_df['neighbors_exalts']

        # Flag as outlier if it deviates more than the threshold
        neighbors_df['is_outlier'] = neighbors_df['price_deviation'] > threshold

        cleaned_df = neighbors_df[~neighbors_df['is_outlier']]
        cleaned_df = cleaned_df.drop(columns=['neighbors_exalts', 'price_deviation', 'is_outlier'])

        df = pd.concat([standalones_df, cleaned_df])
        df.reset_index(inplace=True, drop=True)

        return df

    def fit_nearest_neighbor(self,
                             col_weights: dict):
        cols = df.columns

        scaler = StandardScaler()
        fit_data = scaler.fit_transform(df)

        fit_df = pd.DataFrame(fit_data)
        fit_df.columns = cols

        for col, weighting in col_weights.items():
            col = utils.normalize_column_name(col)
            fit_df[col] = fit_df[col] * weighting

        regressor = RadiusNeighborsRegressor(radius=radius, weights='distance')
        regressor.fit(features, self.prices)
        dxs, indices = regressor.radius_neighbors(features)

        # The first value for dxs and indices is the point itself. We only want neighbors
        indices = [subarray[1:] for subarray in indices]
        prices = [
            [self.prices.iloc[index] for index in subarray]
            for subarray in indices
        ]

    def prep_data(self):
        self.df_parts.features = self._filter_insignificant_columns()
        
        correlation_results = CorrelationAnalyzer.transform_columns_by_correlation(single_correlation_threshold=0.25,
                                                                                   pair_correlation_threshold=0.25)
        self.df_parts.features = correlation_results.transformed_features

        self.fit_nearest_neighbor(col_weights={**correlation_results.single_weights,
                                               **correlation_results.pair_weights})

