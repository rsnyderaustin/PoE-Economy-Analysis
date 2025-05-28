from data_transforming import ListingsTransforming
from file_management import FilesManager
from instances_and_definitions import ModifiableListing
from shared.logging import LogsHandler, LogFile, log_errors


price_predict_log = LogsHandler().fetch_log(LogFile.PRICE_PREDICT_MODEL)


class PricePredictor:
    def __init__(self, files_manager: FilesManager):
        self._files_manager = files_manager

        self._loaded_models = {}

    @log_errors(price_predict_log)
    def predict(self, listing: ModifiableListing) -> float:
        model = self._loaded_models[listing.item_atype]
        df = ListingsTransforming.to_price_predict_df(listings=[listing],
                                                      existing_model=model)

        if df.empty:
            raise ValueError("Listing transformation failed; resulting dataframe is empty.")

        if listing.item_atype not in self._loaded_models:
            self._loaded_models[listing.item_atype] = self._files_manager.load_price_predict_model(listing.item_atype)

        features = df.drop(columns=["divs"], errors="ignore")  # drop target/label if present

        cols_missing_from_model = [col for col in features if col not in model.features]
        if cols_missing_from_model:
            raise ValueError(f"Columns {cols_missing_from_model} in this listing but not in model. Model training data is "
                             f"therefore incomplete.")

        # Ensure all model-required columns exist in features
        cols_missing_from_listing = [col for col in model.features if col not in features]
        for col in cols_missing_from_listing:
            features[col] = None  # fill in with 0 indicating the mod is not present

        # Make sure the column order matches what the model expects
        features = features[model.features]

        prediction = model.predict(features)
        return float(prediction[0])
