import logging

from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
import pandas as pd
from itertools import combinations


class StatsPrep:

    def __init__(self, atype: str, df: pd.DataFrame):
        self.atype = atype
        self.df = df.select_dtypes(include=['int64', 'float64'])

    def _find_correlating_single_columns(self, min_correlation: float) -> set[str]:
        df = self.df.drop(columns=['exalts'])
        corrs = df.corrwith(self.df['exalts'])
        viable_corrs = corrs[corrs >= min_correlation]

        cols = set(viable_corrs.keys())
        return cols

    def _find_correlating_pair_columns(self, min_correlation: float) -> set[tuple]:
        non_price_cols = [col for col in self.df.columns if col != 'exalts']
        mod_combinations = list(combinations(non_price_cols, 2))

        pair_dfs = {
            (mod1, mod2): self.df[(self.df[mod1] > 0) & (self.df[mod2] > 0)]
            for mod1, mod2 in mod_combinations
        }
        valid_pairs = set()
        for (mod1, mod2), filteered_df in pair_dfs.items():
            combo_df = pd.DataFrame({
                mod_pair: filter_df[mod1] * filter_df[mod2],
                'exalts': filter_df['exalts']
            })
            prices = combo_df['exalts']
            combo_df.drop(columns=['exalts'])
            pair_coor = combo_df.corrwith(prices)
            corr_val = pair_coor[mod_pair]
            logging.info(f"{mod_pair} correlation: {corr_val}")
            if corr_val >= min_correlation:
                valid_pairs.add(mod_pair)

        return valid_pairs

    def _plot_correlations(self, df: pd.DataFrame):
        df = df.drop(columns=['exalts'], errors='ignore')
        corr = df.corrwith(self.df['exalts'])
        plt.figure(figsize=(8, 6))
        plt.title(f'{self.atype}')
        sns.heatmap(corr, annot=True, cmap='coolwarm')
        plt.show()

    def prep_data(self):
        pairs = self._find_correlating_pair_columns(min_correlation=0.2)
        standalones = self._find_correlating_single_columns(min_correlation=0.3)

        valid_pairs = set(pair for pair in pairs if pair[0] not in standalones and pair[1] not in standalones)

        corrs = dict()
        for mod1, mod2 in valid_pairs:
            corrs[(mod1, mod2)] = self.df[mod1] * self.df[mod2]

        for col in standalones:
            corrs[col] = self.df[col]

        df = pd.DataFrame(corrs)
        self._plot_correlations(df)


