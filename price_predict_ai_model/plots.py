import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors



def plot_pca(features_df: pd.DataFrame, price_column: pd.Series, title: str, should_plot=True):
    if not should_plot:
        return
    features_df = features_df.copy()
    features_df.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in features_df.columns]
    pca = PCA(n_components=2)
    pca_components = pca.fit_transform(features_df)
    pca_df = pd.DataFrame(pca_components, columns=['pca1', 'pca2'])
    pca_df['price'] = price_column
    plt.figure(figsize=(10, 7))
    c_palette = sns.color_palette("flare", as_cmap=True)
    sns.scatterplot(data=pca_df, x='pca1', y='pca2', hue='price', palette=c_palette, edgecolor='black')
    plt.title(title)
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend(title='price')
    plt.show()


def number_of_neighbors_histogram(neighborhoods, title: str, should_plot=True):
    if not should_plot:
        return
    num_neighbors = [len(n.neighbors) for n in neighborhoods]
    plt.hist(num_neighbors, bins=100, edgecolor='k')
    plt.title(title)
    plt.xlabel('Neighbors')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.xlim(0, 20)
    plt.xticks(np.linspace(0, 20, num=20))
    plt.show()


def neighbor_distances_histogram(neighborhoods, title: str, should_plot=True):
    if not should_plot:
        return
    distances = [
        neighbor.distance
        for neighborhood in neighborhoods
        for neighbor in neighborhood.neighbors
    ]
    plt.hist(distances, bins=100, edgecolor='k')
    plt.title(title)
    plt.xlabel('Distance')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.xlim(0, 1)
    plt.xticks(np.linspace(0, 1, num=20))
    plt.show()


def _bar_plot_feature_diff(neighborhood, neighbor, should_plot=True):
    if not should_plot:
        return
    feature_names = neighborhood.feature_names
    main_point = pd.Series(neighborhood.list_data, index=feature_names)
    neighbor_point = pd.Series(neighbor.data, index=feature_names)
    main_norm = pd.Series(neighborhood.normalized_list_data, index=feature_names)
    neighbor_norm = pd.Series(neighbor.normalized_data, index=feature_names)
    filtered_cols = [col for col in feature_names if (main_point[col] != 0) or (neighbor_point[col] != 0)]
    if not filtered_cols:
        print("No non-zero features to plot.")
        return
    main_vals = main_norm[filtered_cols].astype(float)
    neighbor_vals = neighbor_norm[filtered_cols].astype(float)
    max_vals = pd.concat([main_vals, neighbor_vals], axis=1).max(axis=1)
    max_vals_replaced = max_vals.replace(0, 1)
    norm_main = (main_vals / max_vals_replaced)
    norm_neighbor = (neighbor_vals / max_vals_replaced)
    y = np.arange(len(filtered_cols))
    height = 0.35
    fig, ax = plt.subplots(figsize=(10, max(6, int(len(filtered_cols) * 0.3))))
    ax.barh(y - height / 2, norm_main, height, label='Main (normalized)', color='blue')
    ax.barh(y + height / 2, norm_neighbor, height, label='Neighbor (normalized)', color='red')
    ax.set_yticks(y)
    ax.set_yticklabels(filtered_cols)
    ax.set_xlabel('Normalized Feature Value')
    ax.set_title(f"Neighbor Attributes (Distance: {round(neighbor.distance, 3)}")
    ax.legend()
    plt.tight_layout()
    plt.show(block=True)
    plt.pause(3)


def neighbor_features_comparison(neighborhoods, title: str, should_plot=True):
    if not should_plot:
        return
    for neighborhood in neighborhoods:
        if len(neighborhood.neighbors) == 0:
            continue
        for neighbor in neighborhood.neighbors:
            _bar_plot_feature_diff(neighborhood=neighborhood, neighbor=neighbor)


def binned_median(df, col_name: str, price_col_name: str, title: str, bin_width, should_plot=True):
    if not should_plot:
        return

    if col_name not in df.columns:
        print(f"{col_name} not found in dataframe.")
        return

    df = df.copy()
    df['bin'] = (df[col_name] // bin_width) * bin_width
    grouped = df.groupby('bin')[price_col_name].median().reset_index()

    plt.figure(figsize=(10, 5))
    plt.plot(grouped['bin'], grouped[price_col_name], marker='o', linestyle='-')
    plt.xlabel(f'{col_name} (binned)')
    plt.ylabel(f'Median {price_col_name}')
    plt.title(title)
    plt.grid(True)
    plt.show()


def histogram(series, bins=30, title=None, xlabel=None, ylabel='Frequency', color='blue', should_plot=True):
    if not should_plot:
        return
    plt.figure(figsize=(8, 5))
    plt.hist(series.dropna(), bins=bins, color=color, edgecolor='black')
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(axis='y', alpha=0.75)
    plt.show()
