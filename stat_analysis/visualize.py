import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors

from .neighborhood_class import Neighborhood, Neighbor


def plot_correlations(df: pd.DataFrame, atype: str):
    df = df.drop(columns=['divs'], errors='ignore')
    corr = df.corr()
    plt.figure(figsize=(8, 6))
    plt.title(f'{atype}')
    sns.heatmap(corr, annot=True, cmap='coolwarm')
    plt.show()


def plot_dimensions(df: pd.DataFrame, price_column: str, atype: str):
    for col in df.columns:
        if col == price_column:
            continue

        plt.figure(figsize=(8, 6))
        plt.title(f'{atype}_{col}')
        sns.scatterplot(x=df[col], y=df[price_column])
        plt.show()


def plot_pca(features_df: pd.DataFrame, price_column: str):
    pca = PCA(n_components=2)
    prices = features_df[price_column]
    features_df = features_df.drop(columns=[price_column])

    pca_components = pca.fit_transform(features_df)
    pca_df = pd.DataFrame(pca_components, columns=['pca1', 'pca2'])
    pca_df[price_column] = prices

    # Plot the clusters
    plt.figure(figsize=(10, 7))
    c_palette = sns.color_palette("flare", as_cmap=True)
    # plot_df.loc[plot_df['cluster'] == -1, 'cluster'] = 999
    sns.scatterplot(data=pca_df, x='pca1', y='pca2', hue=price_column, palette=c_palette, edgecolor='black')

    # Customize the plot
    plt.title("Clusters of Mod Combinations (Excluding Price) Based on PCA Components")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.legend(title='divs')
    plt.show()


def plot_avg_distance_to_nearest_neighbor(features_df):
    nn = NearestNeighbors(n_neighbors=2)
    nn.fit(features_df)
    distances, _ = nn.kneighbors(features_df)

    # distances[:, 1] gives the distance to the nearest *other* point
    plt.hist(distances[:, 1], bins=100, edgecolor='k')
    plt.title("Distance to nearest neighbor")
    plt.xlabel("Distance")
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.show()


def plot_all_nearest_neighbors(neighborhoods: list[Neighborhood]):
    distances = [
        neighbor.distance
        for neighborhood in neighborhoods
        for neighbor in neighborhood.neighbors
    ]

    plt.hist(distances, bins=100, edgecolor='k')
    plt.title('Histogram of Distance to Nearest Neighbor')
    plt.xlabel('Distance')
    plt.ylabel('Frequency')
    plt.grid(True)

    # Focus only on 0–5 range
    plt.xlim(0, 1)

    # Add more x-axis labels (ticks)
    plt.xticks(np.linspace(0, 1, num=20))  # e.g., [0.0, 0.5, 1.0, ..., 5.0]

    plt.show()


def radar_plot_neighbors(features_df: pd.DataFrame, indices):
    for main_i in list(range(len(features_df))):
        main_point = features_df.iloc[main_i]
        neighbor_idxs = indices[main_i][1:]  # skip self
        neighbors = features_df.iloc[neighbor_idxs]
        _indiv_radar_plot(main_point=main_point,
                          neighbors=neighbors,
                          feature_names=features_df.columns)


def _indiv_radar_plot(main_point, neighbors, feature_names, title="Feature Comparison"):
    num_vars = len(feature_names)

    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))

    def add_line(values, label, style):
        values = values.tolist()
        values += values[:1]
        ax.plot(angles, values, style, label=label)
        ax.fill(angles, values, alpha=0.1)

    add_line(main_point, "Main Point", "b-")

    for i in range(len(neighbors)):
        neighbor = neighbors.iloc[i]
        add_line(neighbor, f"Neighbor {i + 1}", "r--")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(feature_names)
    ax.set_title(title)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    plt.show()


def bar_plot_neighbors(neighborhoods: list[Neighborhood]):
    for neighborhood in neighborhoods:
        if len(neighborhood.neighbors) == 0:
            continue

        for neighbor in neighborhood.neighbors:
            _bar_plot_feature_diff(neighborhood=neighborhood,
                                   neighbor=neighbor)


def _bar_plot_feature_diff(neighborhood: Neighborhood,
                           neighbor: Neighbor):
    feature_names = neighborhood.feature_names

    # Wrap arrays in labeled Series
    main_point = pd.Series(neighborhood.main_point, index=feature_names)
    neighbor_point = pd.Series(neighbor.data, index=feature_names)
    main_norm = pd.Series(neighborhood.normalized_main_point, index=feature_names)
    neighbor_norm = pd.Series(neighbor.normalized_data, index=feature_names)

    # Only keep features where either point is non-zero
    filtered_cols = [col for col in feature_names
                     if (main_point[col] != 0) or (neighbor_point[col] != 0)]

    if not filtered_cols:
        print("No non-zero features to plot.")
        return

    # Filter and convert to float
    main_vals = main_norm[filtered_cols].astype(float)
    neighbor_vals = neighbor_norm[filtered_cols].astype(float)

    # Normalize each pair
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
