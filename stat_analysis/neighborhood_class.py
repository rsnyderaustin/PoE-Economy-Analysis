import numpy as np
import pandas as pd


class Neighbor:

    def __init__(self,
                 data,
                 normalized_data,
                 price,
                 distance
                 ):
        self.data = data
        self.normalized_data = normalized_data
        self.price = price
        self.distance = distance


class Neighborhood:

    def __init__(self,
                 list_index,
                 list_data,
                 normalized_list_data,
                 list_price,
                 neighbors_data,
                 normalized_neighbors_data,
                 prices,
                 distances,
                 feature_names):
        self.list_index = list_index
        self.list_data = pd.Series(list_data, index=feature_names)
        self.normalized_list_data = pd.Series(normalized_list_data, index=feature_names)
        self.list_price = list_price
        self.feature_names = feature_names

        self.neighbors = [
            Neighbor(data=n, normalized_data=nd, price=p, distance=d)
            for n, nd, p, d in zip(neighbors_data, normalized_neighbors_data, prices, distances)
        ]
        self.neighbors = sorted(self.neighbors, key=lambda n: n.distance)

    def filter_distant_neighbors(self, distance):
        self.neighbors = [n for n in self.neighbors if n.distance < distance]

    def is_outlier(self, min_neighbors: int):
        if len(self.neighbors) < min_neighbors:
            return True

        # Sort neighbors by price
        sorted_neighbors = sorted(self.neighbors, key=lambda n: n.price)

        # Calculate weights
        weights = np.array([1 / (n.distance + 0.1) for n in sorted_neighbors])
        prices = np.array([n.price for n in sorted_neighbors])

        # Normalize weights to sum to 1
        total_weight = np.sum(weights)
        normalized_weights = weights / total_weight

        # Cumulative weights (like a CDF)
        cumulative_weights = np.cumsum(normalized_weights)

        # Find indices corresponding to bottom 10% and top 35%
        lower_idx = np.searchsorted(cumulative_weights, 0.05)
        upper_idx = np.searchsorted(cumulative_weights, 0.4)

        # Compare price against those thresholds
        if self.list_price < prices[lower_idx]:
            return True
        if self.list_price > prices[upper_idx]:
            return True

        return False
