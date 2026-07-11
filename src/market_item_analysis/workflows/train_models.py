from src.market_item_analysis.data_handling import ListingBuilder
from src.market_item_analysis.shared.io_manager import IoManager
from src.market_item_analysis.trade_api.api_response_obj import ApiResponse


class ModelsTrainer:

    def __init__(self,
                 io_manager: IoManager):
        self._io_manager = io_manager

    def train(self):
        raw_responses = self._io_manager.load_raw_responses()
        responses = [ApiResponse(r) for r in raw_responses]
        listings = [ListingBuilder.build_listing(r) for r in responses]
