
import pandas as pd

class ModelData:

    def __init__(self,
                 df: pd.DataFrame,
                 price_column_name: str,
                 log_price_column_name: str):
        self.df: pd.DataFrame = df
        self.price_column_name = price_column_name
        self.log_price_column_name = log_price_column_name

    @property
    def features_df(self) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("Cannot create features DataFrame when self.df is None")

        non_feature_cols = [col for col in [self.price_column_name, self.log_price_column_name]
                            if col is not None]
        features_df = self.df.drop(non_feature_cols)
        return features_df
