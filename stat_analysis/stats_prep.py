import logging
import itertools

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.neighbors import RadiusNeighborsRegressor
from sklearn.preprocessing import StandardScaler

from . import utils


class CorrelationAnalysis:

    def __init__(self,
                 df: pd.DataFrame,
                 price_column: str,
                 min_single_correlation: float,
                 min_pair_correlation: float):
        self.df = df.drop(columns=[price_column])
        self.prices = df[price_column]

        self.single_corr = min_single_correlation
        self.pair_corr = min_pair_correlation

    def _determine_suitable_single_columns(self):
        df = utils.filter_blank_columns(self.df)
        corrs = df.corrwith(self.prices)
        mods = []
        for mod, corr in corrs.items():
            if corr >= self.single_corr:
                mods.append(mod)

        return mods

    def _determine_suitable_pair_columns(self) -> dict:
        df = utils.filter_blank_columns(self.df)

        mod_combinations = list(itertools.combinations(df.columns, 2))

        # Step 1: Build initial dictionary of DataFrames filtered by nonzero indices
        filtered_dfs = {
            (mod1, mod2): self.df[utils.get_nonzero_indices(self.df, [mod1, mod2])]
            for mod1, mod2 in mod_combinations
        }

        # Step 2: Filter out DataFrames with fewer than 30 samples
        pair_dfs = {pair: df[[pair[0], pair[1]]] for pair, df in filtered_dfs.items() if len(df) >= 30}

        # Step 3: Determine how each mod pair correlates with the price of the item
        valid_pairs = dict()
        for (mod1, mod2), pair_df in pair_dfs.items():
            # Create a dataframe with a single column that is the product of mod columns
            product_df = pd.DataFrame({(mod1, mod2): pair_df[mod1] * pair_df[mod2]})

            pair_corr = product_df.corrwith(self.prices)
            corr_val = pair_corr[(mod1, mod2)]
            if corr_val >= self.pair_corr:
                logging.info(f"{(mod1, mod2)} correlation: {corr_val}")
                valid_pairs[(mod1, mod2)] = corr_val

        return valid_pairs

    def transform_columns_by_correlation(self):



class StatsPrep:

    def __init__(self, atype: str, df: pd.DataFrame, price_column: str):
        self.atype = atype
        self.df = df.select_dtypes(include=['int64', 'float64'])
        self.price_column = price_column

    def plot_correlations(self, df: pd.DataFrame):
        df = df.drop(columns=['exalts'], errors='ignore')
        corr = df.corr()
        plt.figure(figsize=(8, 6))
        plt.title(f'{self.atype}')
        sns.heatmap(corr, annot=True, cmap='coolwarm')
        plt.show()

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

    def filter_insignificant_columns(self, variance_threshold: float, correlation_threshold) -> pd.DataFrame:
        non_blank_cols = self.df.columns[(self.df > 0).any() & (~self.df.isna()).any()]
        self.df = self.df[non_blank_cols]

        # Filter out columns that have less than 30 values that are not the mode value
        invalid_cols = []
        for col in self.df.columns:
            most_frequent_value = self.df[col].mode()[0]

            non_constant_count = self.df[self.df[col] != most_frequent_value].count()
            if non_constant_count < 30:
                invalid_cols.append(col)
                continue

            variance = non_constant_count / len(self.df)
            if variance >= variance_threshold:  # If there's enough non-mode values then this column is okay
                continue

            variance_df = self.df[self.df[col] != most_frequent_value]
            corr_val = variance_df.corrwith(self.prices)


    def _filter_out_outliers(self, df, radius=0.2, price_column='exalts', min_neighbors: int = 3, threshold=0.25):
        df = df.copy()
        df = df.dropna(axis=1, how='all')
        df = df.loc[:, df.nunique() > 1]
        prices = df[price_column].values
        features = df.drop(columns=[price_column])

        regressor = RadiusNeighborsRegressor(radius=radius, weights='distance')
        regressor.fit(features, prices)
        dxs, indices = regressor.radius_neighbors(features)

        # The first value for dxs and indices is the point itself. We only want neighbors
        dxs = [subarray[1:] for subarray in dxs]
        indices = [subarray[1:] for subarray in indices]
        prices = [
            [df[price_column].iloc[index] for index in subarray]
            for subarray in indices
        ]

        valid_indices = [i for i, subarray in enumerate(prices) if len(subarray) >= min_neighbors]
        invalid_indices = [i for i, subarray in enumerate(prices) if len(subarray) < min_neighbors]
        standalones_df = df.iloc[invalid_indices]
        n_df = df.iloc[valid_indices]

        n_df.reset_index(drop=True)
        sorted_prices = [np.sort(subarray) for subarray in prices if len(subarray) >= min_neighbors]
        bottom_3_prices = [
            np.median(subarray[:3])
            for subarray in sorted_prices
        ]
        # medians = [np.median(subarray) for subarray in prices if len(subarray) >= min_neighbors]
        n_df['neighbors_exalts'] = bottom_3_prices

        # Calculate price deviation
        n_df['price_deviation'] = np.abs(n_df[price_column] - n_df['neighbors_exalts']) / n_df['neighbors_exalts']

        # Flag as outlier if it deviates more than the threshold
        n_df['is_outlier'] = n_df['price_deviation'] > threshold

        cleaned_df = n_df[~n_df['is_outlier']]
        cleaned_df = cleaned_df.drop(columns=['neighbors_exalts', 'price_deviation', 'is_outlier'])

        df = pd.concat([standalones_df, cleaned_df])
        df.reset_index(inplace=True, drop=True)

        return df

    def _find_outliers(self, pair_weights: dict, standalone_weights: dict):
        scaler = StandardScaler()
        standalone_cols = list(standalone_weights.keys())
        pair_cols = list(pair_weights.keys())

        interaction_df = pd.DataFrame({
            (mod1, mod2): self.df[mod1] * self.df[mod2] for mod1, mod2 in pair_cols
        })
        interaction_df = pd.concat([self.df[standalone_cols], interaction_df], axis=1)

        interaction_df.columns = [_normalize_col(col) for col in interaction_df.columns]
        cols = interaction_df.columns

        fit_data = scaler.fit_transform(interaction_df)
        fit_df = pd.DataFrame(fit_data)
        fit_df.columns = cols
        for col, weighting in {**pair_weights, **standalone_weights}.items():
            col = _normalize_col(col)
            fit_df[col] = fit_df[col] * (1 - weighting)

        fit_df = fit_df.fillna(0)

        fit_df['exalts'] = self.df['exalts']

        # self._plot_pca(df=fit_df)

        cleaned_df = self._filter_out_outliers(df=fit_df)
        return cleaned_df
    
    def _determine_dimension_sum(self, df: pd.DataFrame, pair_weights: dict, standalone_weights: dict):
        scaler = StandardScaler()
        standalone_cols = list(standalone_weights.keys())
        pair_cols = list(pair_weights.keys())

        interaction_df = pd.DataFrame({
            (mod1, mod2): df[mod1] * df[mod2] for mod1, mod2 in pair_cols
        })
        interaction_df = pd.concat([df[standalone_cols], interaction_df], axis=1)

        interaction_df.columns = [_normalize_col(col) for col in interaction_df.columns]
        cols = interaction_df.columns

        fit_data = scaler.fit_transform(interaction_df)
        fit_df = pd.DataFrame(fit_data)
        fit_df.columns = cols
        for col, weighting in {**pair_weights, **standalone_weights}.items():
            col = _normalize_col(col)
            fit_df[col] = fit_df[col] * weighting

        fit_df['exalts'] = df['exalts']
        return fit_df

    def prep_data(self):



