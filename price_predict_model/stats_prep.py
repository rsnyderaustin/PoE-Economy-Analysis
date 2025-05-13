import itertools
import logging
from scipy.spatial.distance import pdist, squareform
from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
import pandas as pd
from itertools import combinations


def _normalize_col(col: tuple | str):
    if isinstance(col, tuple):
        return f"{col[0]}_{col[1]}"

    return col

class StatsPrep:

    def __init__(self, atype: str, df: pd.DataFrame):
        self.atype = atype
        self.df = df.select_dtypes(include=['int64', 'float64'])

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

    def _plot_correlations(self, df: pd.DataFrame):
        df = df.drop(columns=['exalts'], errors='ignore')
        corr = df.corr()
        plt.figure(figsize=(8, 6))
        plt.title(f'{self.atype}')
        sns.heatmap(corr, annot=True, cmap='coolwarm')
        plt.show()

    def _plot_pca(self, original_df: pd.DataFrame, mod_data_df: pd.DataFrame):
        pca = PCA(n_components=2)
        reduced_data = pca.fit_transform(mod_data_df)

        # Add the cluster labels to the reduced data (so we can color the points by cluster)
        original_df['pca1'] = reduced_data[:, 0]
        original_df['pca2'] = reduced_data[:, 1]

        num_colors = len(original_df['cluster'].unique())
        # Plot the clusters
        plt.figure(figsize=(10, 7))
        c_palette = sns.color_palette("pastel", num_colors)
        plot_df = original_df.copy()
        plot_df.drop(columns=['exalts'], inplace=True)
        # plot_df.loc[plot_df['cluster'] == -1, 'cluster'] = 999
        sns.scatterplot(data=plot_df, x='pca1', y='pca2', hue='cluster', palette=c_palette, edgecolor='black')

        # Customize the plot
        plt.title("Clusters of Mod Combinations (Excluding Price) Based on PCA Components")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.legend(title='Cluster')
        plt.show()

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


        """inputs = [
            (eps, min_samples)
            for eps, min_samples in list(itertools.product(
                [0.05, 0.1, 0.15, 0.2, 0.25],
                [3, 4, 5, 7, 10]
            ))
        ]
        for eps, min_samples in inputs:
        logging.info(f"Eps: {eps}, Min Samples: {min_samples}")"""
        dbscan = DBSCAN(eps=0.05, min_samples=3)  # These values are adjustable
        labels = dbscan.fit_predict(fit_df)

        fit_df['cluster'] = labels
        fit_df['exalts'] = self.df['exalts']
        # self._plot_pca(original_df=df, mod_data_df=mod_data)

        logging.info(f"\tNum clusters: {len(fit_df['cluster'].unique())}")
        outlier_indices = []
        for cluster_id in fit_df['cluster'].unique():
            if cluster_id == -1:
                continue  # Skip noise points

            cluster_df = fit_df[fit_df['cluster'] == cluster_id]

            """plt.figure(figsize=(10, 5))
            sns.boxplot(x=cluster_df['exalts'])
            plt.title("Exalts Distribution with IQR Detection")
            plt.show()"""

            # IQR Method to detect outliers
            q1 = cluster_df['exalts'].quantile(0.25)
            q3 = cluster_df['exalts'].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Collect outlier indices
            outliers = cluster_df[(cluster_df['exalts'] < lower_bound) | (cluster_df['exalts'] > upper_bound)]
            logging.info(f"\tCluster: filtered out {len(outliers)} listings out of {len(cluster_df)}")
            outlier_indices.extend(outliers.index)

        # Step 4: Drop outliers from the original DataFrame
        df_clean = fit_df.drop(index=outlier_indices)
        return df_clean

    def prep_data(self):
        pair_corrs = self._find_correlating_pair_columns(min_correlation=0.25)
        standalone_corrs = self._find_correlating_single_columns(min_correlation=0.25)

        cleaned_df = self._find_outliers(pair_weights=pair_corrs, standalone_weights=standalone_corrs)
        logging.info(f"Atype {self.atype} data prep\n\tStart listings: {len(self.df)}\n\tEnd listings: {len(cleaned_df)}")
        return cleaned_df


