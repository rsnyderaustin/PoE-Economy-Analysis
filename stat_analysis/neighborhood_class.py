

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
                 main_point,
                 normalized_main_point,
                 neighbors_data,
                 normalized_neighbors_data,
                 prices,
                 distances,
                 feature_names):
        self.main_point = main_point
        self.normalized_main_point = normalized_main_point
        self.feature_names = feature_names

        self.neighbors = [
            Neighbor(data=n, normalized_data=nd, price=p, distance=d)
            for n, nd, p, d in zip(neighbors_data, normalized_neighbors_data, prices, distances)
        ]

    def filter_distant_neighbors(self, distance):
        self.neighbors = [n for n in self.neighbors if n.distance < distance]
