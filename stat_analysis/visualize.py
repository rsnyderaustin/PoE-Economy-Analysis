import pandas as pd
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
import seaborn as sns


def plot_correlations(df: pd.DataFrame, atype: str):
    df = df.drop(columns=['exalts'], errors='ignore')
    corr = df.corr()
    plt.figure(figsize=(8, 6))
    plt.title(f'{atype}')
    sns.heatmap(corr, annot=True, cmap='coolwarm')
    plt.show()


def plot_dimensions(df: pd.DataFrame, atype: str):
    for col in df.columns:
        if col == 'exalts':
            continue

        plt.figure(figsize=(8, 6))
        plt.title(f'{atype}_{col}')
        sns.scatterplot(x=df[col], y=df['exalts'])
        plt.show()


def plot_pca(features_df: pd.DataFrame):
    pca = PCA(n_components=2)
    pca_df = pd.DataFrame(features_df, columns=['pca1', 'pca2'])

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


def visualize_neighbors_regression(features_df: pd.DataFrame,
                                   prices: pd.Series,
                                   distances,
                                   indices):
    """

    :param features_df: A denormalized DataFrame of features
    :param prices:
    :param distances:
    :param indices:
    :return:
    """
    data = {
        'index': [],
        'distance': [],
        'neighbor_price': [],
        'listing_price': [],
        **{f"mainpoint_{f}": [] for f in features_df.columns},
        **{f: [] for f in features_df.columns}
    }
    # Display the neighbors
    inputs = list(zip(distances, indices))
    for main_i, (dx_to_ns, idxs) in enumerate(inputs):
        # Get the features of the main point
        main_point_features = features_df.iloc[main_i].values

        # Loop through each neighbor index and corresponding distance
        for dx, idx in zip(dx_to_ns, idxs):
            data['index'].append(main_i)
            data['listing_price'].append(prices.iloc[main_i])
            data['neighbor_price'].append(prices.iloc[idx])
            data['distance'].append(dx)
            for i, col in enumerate(features_df.columns):
                data[f"mainpoint_{col}"].append(main_point_features[i])

            neighbor_features = features_df.iloc[idx]
            for col, val in neighbor_features.items():
                data[col].append(val)

        if main_i >= 250:  # Doing all rows takes forever, so we just stop after 250
            break

    neighbors_df = pd.DataFrame(data)
    return neighbors_df
