import logging

import pandas as pd

from src.market_item_analysis.data_handling import ListingBuilder
from src.market_item_analysis.listing.flattener import ListingFlattener
from src.market_item_analysis.core.io_manager import IoManager
from src.market_item_analysis.trade_api.trade_result import ApiResponse

logger = logging.getLogger(__name__)


class TrainingDataCreator:

    def __init__(self, io_manager: IoManager):
        self._io_manager = io_manager

    def create(self) -> pd.DataFrame:
        raw_listings_data = self._io_manager.load_raw_responses()
        responses = [ApiResponse(r) for r in raw_listings_data]
        listings = [ListingBuilder.from_api_response(r) for r in responses]
        flattened_listing_dicts = [ListingFlattener.flatten_listing(l) for l in listings]

        aggregate_d = dict()
        d_len = 0
        for d in flattened_listing_dicts:
            missing_keys = [k for k in d.keys() if k not in aggregate_d]
            none_l = [None] * d_len
            aggregate_d.update({k: none_l for k in missing_keys})

            for k, v in d.items():
                d[k].append(v)

        return pd.DataFrame(aggregate_d)
