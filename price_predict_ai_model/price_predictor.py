from file_management import FilesManager, ModelPath
import data_transforming
from instances_and_definitions import ModifiableListing


class PricePredictor:

    def __init__(self):
        files_manager = FilesManager()
        self.predict_model = files_manager.model_data[ModelPath.PRICE_PREDICT_MODEL]

    def predict_prices(self, listings: list[ModifiableListing]) -> list:
        listings_df = data_transforming.ListingsTransforming.to_price_predict_df(listings=listings)

        listings_df = listings_df.drop(columns=['exalts'])

        listings_df = listings_df[self.predict_model.feature_names]
        dmatrix = xgb.DMatrix(listings_df, enable_categorical=True)
        predicts = self.predict_model.predict(dmatrix)

        return list(predicts)

