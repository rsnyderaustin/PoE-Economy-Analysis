from matplotlib import pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
import pandas as pd
from itertools import combinations

import price_predict_model
from price_predict_model.stats_prep import StatsPrep
from file_management import FileKey, FilesManager
from operations_coordination.operations_coordinator import OperationsCoordinator

listing_data = FilesManager().file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING]
df = price_predict_model.PricePredictDataManager().export_data_for_model(which_file=FileKey.CRITICAL_PRICE_PREDICT_TRAINING)

atype_dfs = {
    atype: sub_df for atype, sub_df in df.groupby('atype', observed=True)
}

for atype, df in atype_dfs.items():
    stats_prep = StatsPrep(atype=str(atype),
                           df=df)
    stats_prep.prep_data()
    df.drop(columns=['atype', 'btype', 'rarity', 'corrupted'], inplace=True)
    """corr = df.corr()
    plt.figure(figsize=(8, 6))
    plt.title(f'{str(atype)})')
    sns.heatmap(corr, annot=True, cmap='coolwarm')
    plt.show()

    sns.pairplot(df[['Critical Hit Chance', 'max_quality_pdps',
                     'bow_attacks_fire_#_additional_arrows', '+#%_to_critical_damage_bonus']])
    plt.show()"""

    # Filter out variables that don't correlate significantly with price in any pairwise combo

    combos_df = df.drop(columns=['exalts'])
    mod_combinations = list(combinations(combos_df.columns, 2))
    interaction_corrs = {}
    for mod1, mod2 in mod_combinations:
        interaction_corrs[(mod1, mod2)] = combos_df[mod1] * combos_df[mod2]

    # Create a DataFrame for the interactions
    interaction_df = pd.DataFrame(interaction_corrs)
    exalt_corrs = interaction_df.corrwith(df['exalts'])
    viable_coors = exalt_corrs[exalt_corrs > 0.3]

    viable_cols = ()
    scaler = StandardScaler()
    mod_data = scaler.fit_transform(df.drop(columns=['exalts']))

    for eps in [0.25, 0.5, 0.75, 1, 1.5, 2, 5, 10]:
        dbscan = DBSCAN(eps=eps, min_samples=15)  # These values are adjustable
        labels = dbscan.fit_predict(mod_data)

        df['cluster'] = labels

        pca = PCA(n_components=2)
        reduced_data = pca.fit_transform(mod_data)

        plt.figure(figsize=(10, 7))
        plt.scatter(reduced_data[:, 0], reduced_data[:, 1], c=labels, cmap='viridis', s=10)
        plt.title(f"DBSCAN Clusters of Mod Combinations ({atype})")
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.show()


"""
ops_coord = OperationsCoordinator(refresh_poecd_source=True)
# ops_coord.fill_training_data()
# ops_coord.build_price_predict_model()
ops_coord.find_underpriced_items()
"""