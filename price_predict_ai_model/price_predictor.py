from file_management import FilesManager, ModelPath
import data_transforming
from instances_and_definitions import ModifiableListing
from shared import shared_utils


class PricePredictor:

    def __init__(self):
        files_manager = FilesManager()
        self.predict_model = files_manager.model_data[ModelPath.PRICE_PREDICT_MODEL]

    def predict_price(self, listings: list[ModifiableListing]):
        listings_data = [data_transforming.default_flatten_preset(listing).flattened_data for listing in listings]
        row_data = shared_utils.flatten_data_into_rows(listings_data)
        listings_df = data_transforming.prepare_listings_data_for_model(row_data)

        prices = list(listings_df['exalts'])
        listings_df = listings_df.drop(columns=['exalts'])

        listings_df = listings_df[self.predict_model.feature_names]
        dmatrix = xgb.DMatrix(listings_df, enable_categorical=True)
        predicts = self.predict_model.predict(dmatrix)

