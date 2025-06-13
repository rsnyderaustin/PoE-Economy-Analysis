import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.neighbors import NearestNeighbors


# Assume Neighborhood and Neighbor classes are defined elsewhere

def _apply_log_outliers(row):
    non_null_dict = {col: val for col, val in row.items()
                     if pd.notna(val) and val > 0.0 and col not in ['Predicted Price', 'divs']}

    print(f"\n\n")
    print(f"Predicted Price: {row['Predicted Price']}"
          f"\nActual Price: {row['divs']}"
          f"\n\tAttributes and values:")

    for k, v in non_null_dict.items():
        print(f"\t{k}: {v}")


def log_outliers(outliers_df, should_plot=True):
    if not should_plot:
        return
    outliers_df.apply(_apply_log_outliers, axis=1)


def plot_correlation_matrix(df: pd.DataFrame, should_plot=True):
    if not should_plot:
        return
    corr_df = df.select_dtypes(include=['int64', 'float64'])
    plt.figure(figsize=(18, 8))
    corr_matrix = corr_df.corr()
    sns.heatmap(corr_matrix[['divs']].sort_values(by='divs', ascending=False), annot=True, cmap='coolwarm')
    plt.show()


def plot_feature_importance(model, atype: str, should_plot=True):
    if not should_plot:
        return
    importance = model.get_score(importance_type='weight')
    importance_df = pd.DataFrame(list(importance.items()), columns=['Feature', 'Importance'])
    importance_df = importance_df.sort_values(by='Importance', ascending=False)
    importance_df.plot(kind='barh', x='Feature', y='Importance', legend=False, figsize=(10, 6))
    plt.title(f'Feature Importance for {atype}')
    plt.xlabel('Importance')
    plt.ylabel('Feature')
    plt.show()


def plot_actual_vs_predicted(atype, test_predictions, test_targets, should_plot=True):
    if not should_plot:
        return
    all_values = list(test_predictions) + list(test_targets)
    min_val = min(all_values) * 0.8
    max_val = max(all_values) * 1.2
    plt.figure(figsize=(8, 5))
    plt.scatter(test_predictions, test_targets, alpha=0.5)
    plt.plot([min_val, max_val], [min_val, max_val], color='red', linestyle='--')
    plt.xlabel("Predicted Price (Divs)")
    plt.ylabel("Actual Price (Divs)")
    plt.title(f"Actual vs. Predicted Prices for {atype}")
    plt.xlim(min_val, max_val)
    plt.ylim(min_val, max_val)
    plt.grid(True)
    plt.axis('equal')
    plt.show()


def print_outliers(test_target_df, test_features_df, test_predictions, should_plot=True):
    if not should_plot:
        return
    training_df = pd.concat([test_target_df, test_features_df], axis=1)
    training_df['Predicted Price'] = test_predictions
    training_df['Absolute Error'] = (training_df['Predicted Price'] - training_df['divs']).abs()
    under_priced_df = training_df[training_df['divs'] - training_df['Predicted Price'] < 0]
    outliers_df = under_priced_df.sort_values(by='Absolute Error', ascending=False).head(3)


def plot_correlations(df: pd.DataFrame, atype: str, should_plot=True):
    if not should_plot:
        return
    df = df.drop(columns=['divs'], errors='ignore')
    corr = df.corr()
    plt.figure(figsize=(8, 6))
    plt.title(f'{atype}')
    sns.heatmap(corr, annot=True, cmap='coolwarm')
    plt.show()


def plot_dimensions(df: pd.DataFrame, price_column: str, atype: str, should_plot=True):
    if not should_plot:
        return
    for col in df.columns:
        if col == price_column:
            continue
        plt.figure(figsize=(8, 6))
        plt.title(f'{atype}_{col}')
        sns.scatterplot(x=df[col], y=df[price_column])
        plt.show()


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


def radar_plot_neighbors(features_df: pd.DataFrame, indices, should_plot=True):
    if not should_plot:
        return
    for main_i in list(range(len(features_df))):
        main_point = features_df.iloc[main_i]
        neighbor_idxs = indices[main_i][1:]
        neighbors = features_df.iloc[neighbor_idxs]
        _indiv_radar_plot(main_point=main_point, neighbors=neighbors, feature_names=features_df.columns)


def _indiv_radar_plot(main_point, neighbors, feature_names, title="Feature Comparison", should_plot=True):
    if not should_plot:
        return
    num_vars = len(feature_names)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]
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


def neighbor_features_comparison(neighborhoods, title: str, should_plot=True):
    if not should_plot:
        return
    for neighborhood in neighborhoods:
        if len(neighborhood.neighbors) == 0:
            continue
        for neighbor in neighborhood.neighbors:
            _bar_plot_feature_diff(neighborhood=neighborhood, neighbor=neighbor)


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


def plot_column(col_name,
                price_col_name,
                df: pd.DataFrame,
                should_plot: bool = True,
                figsize=(6, 4),
                transparency=0.7):
    if not should_plot:
        return
    if col_name not in df.columns or price_col_name not in df.columns:
        raise ValueError(f"Column(s) '{col_name}' or '{price_col_name}' not found in dataframe.")
    plt.figure(figsize=figsize)
    plt.scatter(df[col_name], df[price_col_name], alpha=transparency)
    plt.xlabel(col_name)
    plt.ylabel(price_col_name)
    plt.title(f'{price_col_name} vs. {col_name}')
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_binned_median(df, col_name: str, price_col_name: str, title: str, bin_width, should_plot=True):
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


def plot_histogram(series, bins=30, title=None, xlabel=None, ylabel='Frequency', color='blue', should_plot=True):
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
