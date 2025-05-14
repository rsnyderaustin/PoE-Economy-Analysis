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

        self.s_corr = min_single_correlation
        self.m_corr = min_pair_correlation

    def _find_single_columns(self):
        df = utils.filter_blank_columns(self.df)
        corrs = df.corrwith(self.prices)
        mods = []
        for mod, corr in corrs.items():
            if corr >= self.s_corr:
                mods.append(mod)

        return mods

    def _find_valid_correlations(self) -> dict:
        df = utils.filter_blank_columns(self.df)

        mod_combinations = list(itertools.combinations(df.columns, 2))

        pair_dfs = {
            (mod1, mod2): self.df[utils.get_nonzero_indices(df, [mod1, mod2])]
            for mod1, mod2 in mod_combinations
        }
        # Sample size for the pair has to be at least 30
        pair_dfs = {
            mod_pair: df for mod_pair, df in pair_dfs.items() if len(df) >= 30
        }
        valid_pairs = dict()
        for (mod1, mod2), filtered_df in pair_dfs.items():
            combo_df = pd.DataFrame({
                (mod1, mod2): filtered_df[mod1] * filtered_df[mod2],
                'exalts': filtered_df['exalts']
            })
            prices = combo_df['exalts']
            combo_df.drop(columns=['exalts'])
            pair_corr = combo_df.corrwith(prices)
            corr_val = pair_corr[(mod1, mod2)]
            if corr_val >= min_correlation:
                logging.info(f"{(mod1, mod2)} correlation: {corr_val}")
                valid_pairs[(mod1, mod2)] = corr_val

        return valid_pairs

        return mods

    def transform_columns_by_correlation(self):



class StatsPrep:

    def __init__(self, atype: str, df: pd.DataFrame, price_column: str):
        self.atype = atype
        self.df = df.select_dtypes(include=['int64', 'float64'])
        self.price_column = price_column

    def filter_blank_columns(self):
        self.df = self.df.loc[:, ~((self.df.eq(0) | self.df.isna()).all())]
        return self

    def _find_correlating_single_columns(self, min_correlation: float) -> dict:
        df = self.df.drop(columns=['exalts'])

        dfs = {
            mod: self.df[self.df[mod] > 0]
            for mod in df.columns
        }
        mods = dict()
        for mod, df in dfs.items():
            filtered_df = df[[mod, 'exalts']]
            prices = filtered_df['exalts']
            filtered_df = filtered_df.drop(columns=['exalts'])
            corr = filtered_df.corrwith(prices)
            corr_val = corr[mod]
            if corr_val >= min_correlation:
                logging.info(f"{mod} correlation: {corr_val}")
                mods[mod] = corr_val

        return mods

    def _find_correlating_pair_columns(self, min_correlation: float) -> dict:
        non_price_cols = [col for col in self.df.columns if col != 'exalts']
        mod_combinations = list(combinations(non_price_cols, 2))

        pair_dfs = {
            (mod1, mod2): self.df[(self.df[mod1] > 0) & (self.df[mod2] > 0)]
            for mod1, mod2 in mod_combinations
        }
        # Sample size for the pair has to be at least 30
        pair_dfs = {
            mod_pair: df for mod_pair, df in pair_dfs.items() if len(df) >= 30
        }
        valid_pairs = dict()
        for (mod1, mod2), filtered_df in pair_dfs.items():
            combo_df = pd.DataFrame({
                (mod1, mod2): filtered_df[mod1] * filtered_df[mod2],
                'exalts': filtered_df['exalts']
            })
            prices = combo_df['exalts']
            combo_df.drop(columns=['exalts'])
            pair_corr = combo_df.corrwith(prices)
            corr_val = pair_corr[(mod1, mod2)]
            if corr_val >= min_correlation:
                logging.info(f"{(mod1, mod2)} correlation: {corr_val}")
                valid_pairs[(mod1, mod2)] = corr_val

        return valid_pairs

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



