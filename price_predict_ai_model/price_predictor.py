from data_transforming import ListingsTransforming
from file_management import FilesManager
from instances_and_definitions import ModifiableListing


class PricePredictor:
    def __init__(self, files_manager: FilesManager):
        self._files_manager = files_manager

        self._loaded_models = {}

    def predict(self, listing: ModifiableListing) -> float:
        df = ListingsTransforming.to_price_predict_df(listings=[listing])

        if df.empty:
            raise ValueError("Listing transformation failed; resulting dataframe is empty.")

        if listing.item_atype in self._loaded_models:
            model = self._loaded_models[listing.item_atype]
        else:
            model = self._files_manager.load_price_predict_model(listing.item_atype)

        features = df.drop(columns=["exalts"], errors="ignore")  # drop target/label if present

        prediction = model.predict(features)
        return float(prediction[0])
