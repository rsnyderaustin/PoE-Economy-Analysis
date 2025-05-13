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


"""
ops_coord = OperationsCoordinator(refresh_poecd_source=True)
# ops_coord.fill_training_data()
# ops_coord.build_price_predict_model()
ops_coord.find_underpriced_items()
"""