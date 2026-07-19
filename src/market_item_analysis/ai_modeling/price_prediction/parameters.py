

class PricePredictorParameters:

    def __init__(self,
                 training_depth: int = 12,
                 eta: float = 0.00075,
                 num_boost_rounds: int = 1250,
                 early_stopping_rounds: int = 50):
        self.training_depth = training_depth
        self.eta = eta
        self.num_boost_rounds = num_boost_rounds
        self.early_stopping_rounds = early_stopping_rounds