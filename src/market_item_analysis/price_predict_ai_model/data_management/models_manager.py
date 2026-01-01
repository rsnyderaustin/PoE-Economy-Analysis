
import logging

from src.market_item_analysis.price_predict_ai_model import PricePredictor
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory


logger = logging.getLogger(__name__)


class PricePredictorsManager:

    def __init__(self):
        self._predictors_d = dict()

    def fetch_model(self, category: EquipmentCategory) -> PricePredictor | None:
        if category not in self._predictors_d:
            logger.warning(f"{category} does not have a Price Predictor model.")
            return None

        return self._predictors_d[category]