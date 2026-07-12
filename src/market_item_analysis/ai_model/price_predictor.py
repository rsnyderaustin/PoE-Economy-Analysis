
import logging
import pandas as pd

from src.market_item_analysis.data_handling.listing_flattener import ListingFlattener
from src.market_item_analysis.listing.objects import Listing
from src.market_item_analysis.ai_model.data_management.models_manager import PricePredictorsManager

logger = logging.getLogger(__name__)

class PricePredictor:
    def __init__(self, models_manager: PricePredictorsManager):
        self._models_manager = models_manager

    def predict(self, listing: Listing) -> float:
        model = self._models_manager.fetch_model(category=listing.types.item_category)
        flattened_d = ListingFlattener.flatten_listing(listing)

        cols_missing_from_model = [col for col in flattened_d if col not in model.features]
        if cols_missing_from_model:
            raise ValueError(f"Columns {cols_missing_from_model} in this listing but not in model. Model training data is "
                             f"therefore incomplete.")

        cols_missing_from_listing = [col for col in model.features if col not in flattened_d]
        for col in cols_missing_from_listing:
            flattened_d[col] = None  # fill in with 0 indicating the mod is not present

        flattened_d = flattened_d[model.features]

        flattened_df = pd.DataFrame(data=flattened_d)

        if flattened_df.empty:
            raise ValueError("Listing transformation failed; resulting dataframe is empty.")

        prediction = model.predict(features)
        return float(prediction[0])
