import os
from copy import deepcopy
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.decomposition import PCA

from src.market_item_analysis.ai_modeling.stats.data import ListingModelData, ColumnCategory
from src.market_item_analysis.ai_modeling.stats.neighborhood import Neighborhood
from src.market_item_analysis.core.paths import ProjectPathResolver


@classmethod
class PlotSpecs:
    title: str
    show_plot: bool = False
    save_plot: bool = True

class PlotService:
    _OUTPUT_DIR = ProjectPathResolver.path(folders=['files', 'plots'])

    @classmethod
    def _save_plot(cls, file_name: str):
        file_path = cls._OUTPUT_DIR / file_name

        plt.tight_layout()
        plt.savefig(file_path, dpi=150)
        plt.close()

    @classmethod
    def plot_pca(cls, model_data: ListingModelData, plot_specs: PlotSpecs):
        features_df = model_data.filter_by_categories(col_categories=[ColumnCategory.FEATURE])

        pca = PCA(n_components=2)
        pca_components = pca.fit_transform(features_df)
        pca_df = pd.DataFrame(pca_components, columns=['pca1', 'pca2'])
        pca_df['target'] = model_data.target_col
        plt.figure(figsize=(10, 7))
        c_palette = sns.color_palette("flare", as_cmap=True)
        sns.scatterplot(data=pca_df, x='pca1', y='pca2', hue='target', palette=c_palette, edgecolor='black')
        plt.title(plot_specs.title)
        plt.xlabel("PCA Component 1")
        plt.ylabel("PCA Component 2")
        plt.legend(title='target')

        if plot_specs.show_plot:
            plt.show()

        if plot_specs.save_plot:
            cls._save_plot(file_name=plot_specs.title)

    @classmethod
    def number_of_neighbors_histogram(cls, neighborhoods: list[Neighborhood], plot_specs: PlotSpecs):
        num_neighbors = [len(n.neighbors) for n in neighborhoods]
        plt.hist(num_neighbors, bins=100, edgecolor='k')
        plt.title(plot_specs.title)
        plt.xlabel('Neighbors')
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.xlim(0, 20)
        plt.xticks(np.linspace(0, 20, num=20))

        if plot_specs.show_plot:
            plt.show()

        if plot_specs.save_plot:
            cls._save_plot(file_name=plot_specs.title)

    @classmethod
    def neighbor_distances_histogram(cls, neighborhoods, plot_specs: PlotSpecs):
        distances = [
            neighbor.distance
            for neighborhood in neighborhoods
            for neighbor in neighborhood.neighbors
        ]
        plt.hist(distances, bins=100, edgecolor='k')
        plt.title(plot_specs.title)
        plt.xlabel('Distance')
        plt.ylabel('Frequency')
        plt.grid(True)
        plt.xlim(0, 1)
        plt.xticks(np.linspace(0, 1, num=20))

        if plot_specs.show_plot:
            plt.show()

        if plot_specs.save_plot:
            cls._save_plot(file_name=plot_specs.title)

    @classmethod
    def binned_median(cls, model_data: ListingModelData, col_name: str, plot_specs: PlotSpecs, bin_width: int = 60):
        if col_name not in model_data.columns:
            print(f"{col_name} not found in dataframe.")
            return

        model_data = deepcopy(model_data)
        model_data.df['bin'] = (model_data.df[col_name] // bin_width) * bin_width
        grouped = model_data.df.groupby('bin')[model_data.target_col_name].median().reset_index()

        plt.figure(figsize=(10, 5))
        plt.plot(grouped['bin'], grouped[model_data.target_col_name], marker='o', linestyle='-')
        plt.xlabel(f'{col_name} (binned)')
        plt.ylabel(f'Median {model_data.target_col_name}')
        plt.title(plot_specs.title)
        plt.grid(True)

        if plot_specs.show_plot:
            plt.show()

        if plot_specs.save_plot:
            cls._save_plot(file_name=plot_specs.title)

    @classmethod
    def histogram(cls, series: pd.Series, plot_specs: PlotSpecs, bins=30, xlabel=None, ylabel='Frequency', color='blue'):
        plt.figure(figsize=(8, 5))
        plt.hist(series.dropna(), bins=bins, color=color, edgecolor='black')
        if plot_specs.title:
            plt.title(plot_specs.title)
        if xlabel:
            plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.grid(axis='y', alpha=0.75)

        if plot_specs.show_plot:
            plt.show()

        if plot_specs.save_plot:
            cls._save_plot(file_name=plot_specs.title)
