
import data_transforming
from instances_and_definitions import ModifiableListing


class PricePredictor:

    def __init__(self, predict_mode):
        self.predict_model = predict_mode

    def predict_prices(self, listings: list[ModifiableListing]) -> list:
        listings_df = data_transforming.ListingsTransforming.to_price_predict_df(listings=listings)

        listings_df = listings_df.drop(columns=['exalts'])

        listings_df = listings_df[self.predict_model.feature_names]
        dmatrix = xgb.DMatrix(listings_df, enable_categorical=True)
        predicts = self.predict_model.predict(dmatrix)

        return list(predicts)

