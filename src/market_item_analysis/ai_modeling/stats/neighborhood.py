from dataclasses import dataclass

import numpy as np

from src.market_item_analysis.ai_modeling.stats.data import ListingModelData, ColumnCategory


@dataclass(frozen=True)
class Neighbor:
    source_index: int
    neighbor_index: int
    distance: float

@dataclass(frozen=True)
class Neighborhood:
    source_index: int
    neighbors: list[Neighbor]


class NeighborhoodsSearch:

    def __init__(self,
                 model_data: ListingModelData,
                 n_neighbors: int = 100,
                 neighbor_distance_threshold: float = 0.00075):
        self.model_data = copy.deepcopy(model_data)
        self.n_neighbors = n_neighbors
        self.neighbor_distance_threshold = neighbor_distance_threshold
        self._model = KNeighborsRegressor(n_neighbors=n_neighbors, n_jobs=-1)

        self._fit()

    def _fit(self):
        normalized_df = self.model_data.normalize(col_categories=[ColumnCategory.FEATURE])
        self._model.fit(normalized_df)

    def _search_to_model_indices(self, search_indices):
        index_map = np.array(self.model_data.df.index)
        mapped_indices = index_map[search_indices]
        return mapped_indices

    def _exclude_source_from_searches(self, indices, distances):
        final_indices = indices[:, 1:]
        final_distances = distances[:, 1:]

        return final_indices, final_distances

    def get_neighborhoods(self) -> list[Neighborhood]:
        # 1. Perform search
        features = self.model_data.normalize(col_categories=[ColumnCategory.FEATURE])
        distances, indices = self._model.kneighbors(features)

        converted_indices = self._search_to_model_indices(indices)
        indices, distances = self._exclude_source_from_searches(converted_indices, distances)

        neighborhoods = []
        for source_idx, neigh_indices, neigh_distances in zip(self.model_data.df.index, indices, distances):
            neigh_indices = neigh_indices.tolist()
            neigh_distances = neigh_distances.tolist()

            neighbors = []
            for neigh_idx, neigh_dist in zip(neigh_indices, neigh_distances):
                if neigh_dist < self.neighbor_distance_threshold:
                    continue
                neighbors.append(Neighbor(source_index=source_idx,
                                          neighbor_index=neigh_idx,
                                          distance=neigh_dist))
            neighborhoods.append(Neighborhood(source_index=source_idx,
                                              neighbors=neighbors))

        return neighborhoods
