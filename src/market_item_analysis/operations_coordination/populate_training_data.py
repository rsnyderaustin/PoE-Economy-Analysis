import datetime
import os
import logging
import random

import psutil

from src.market_item_analysis import psql
from src.market_item_analysis.data_handling.api_response_gatekeeper import ApiResponseGatekeeper
from src.market_item_analysis.file_management import logging_setup
from src.market_item_analysis.instances_and_definitions.item_instances import EquipmentListing
from src.market_item_analysis.operations_coordination.cache_settings import CacheSettings
from src.market_item_analysis.data_handling import ListingBuilder
from src.market_item_analysis.file_management.io_manager import PoE2EconomyAnalysisIOManager
from src.market_item_analysis.trade_api.api_response_obj import ApiResponse
from src.market_item_analysis.trade_api import TradeApiHandler
from src.market_item_analysis.trade_api.query import QueryPresets

logger = logging.getLogger(__name__)


class TrainingDataPopulator:

    def __init__(self,
                 cache_settings: CacheSettings,
                 trade_api_handler: TradeApiHandler,
                 psql_manager: psql.PostgreSqlManager,
                 io_manager: PoE2EconomyAnalysisIOManager):
        logging_setup.setup_logging()

        self.cache_settings = cache_settings
        self.program_start = datetime.datetime.now()

        self.trade_api_handler = trade_api_handler
        self.psql_manager = psql_manager
        self.io_manager = io_manager

        self._response_gatekeeper = ApiResponseGatekeeper()
        self._listings = []

    """def _filter_old_listings(self, listings: list[EquipmentListing]):
        sorted_listings = sorted(listings, key=lambda l: l.metadata.date_fetched)
        listings_d = {l: l for l in sorted_listings}
        return list(listings_d.values())"""

    def _load_raw_responses_from_file(self):
        raw_api_responses = self.io_manager.load_raw_listings()
        api_responses = [ApiResponse(r) for r in raw_api_responses]

        valid_api_responses = [r for r in api_responses
                               if self._response_gatekeeper.should_process_api_response(r)]

        constructed_file_listings = [ListingBuilder.build_listing(api_response)
                                     for api_response in valid_api_responses]
        self._listings.extend(constructed_file_listings)
        self._response_gatekeeper.add_listings(constructed_file_listings)

    def _load_listings_from_file(self):
        existing_file_listings = self.io_manager.load_constructed_listings()
        self._listings.extend(existing_file_listings)

        self._response_gatekeeper.add_listings(existing_file_listings)

    def _pull_from_trade_api(self):
        pull_start_time = datetime.datetime.now()
        training_queries = QueryPresets.create_training_data_queries()
        random.shuffle(training_queries)

        pulled_raw_responses = 0
        pulled_listings = 0
        newest_raw_listings = []
        newest_listings = []
        for i, raw_responses in enumerate(self.trade_api_handler.fetch_responses(training_queries)):
            newest_raw_listings.extend(raw_responses)
            if self.cache_settings.save_raw_responses_to_file and i != 0 and i % self.cache_settings.save_every == 0:
                self.io_manager.save_raw_responses(newest_raw_listings)
                newest_raw_listings = []

            pulled_raw_responses += len(raw_responses)

            responses = [ApiResponse(r) for r in raw_responses]
            valid_responses = [r for r in responses if self._response_gatekeeper.should_process_api_response(r)]

            new_listings = [ListingBuilder.build_listing(r) for r in valid_responses]
            self._listings.extend(new_listings)
            newest_listings.extend(new_listings)
            pulled_listings += len(new_listings)

            if self.cache_settings.save_listings_to_file and i != 0 and i % self.cache_settings.save_every == 0:
                self.io_manager.save_constructed_listings(newest_listings)
                newest_listings = []

            print(f"\nPulling from Trade API:"
                  f"\nIteration {i}:"
                  f"\n\tAPI responses: {len(raw_responses)}"
                  f"\n\tValid listings created: {len(self._listings)}"
                  f"\nTotal:"
                  f"\n\tAPI responses: {pulled_raw_responses}"
                  f"\n\tValid listings created: {pulled_listings}")

            current_time = datetime.datetime.now()
            runtime_minutes = (current_time - pull_start_time).total_seconds() / 60.0

            if runtime_minutes >= self.cache_settings.pull_time_minutes:
                # Save leftover data if it wasn't just saved
                if i != 0 and i % self.cache_settings.save_every != 0:
                    if self.cache_settings.save_raw_responses_to_file:
                        self.io_manager.save_raw_responses(newest_raw_listings)
                    if self.cache_settings.save_listings_to_file:
                        self.io_manager.save_constructed_listings(newest_listings)

                return

    def populate(self):
        if self.cache_settings.load_raw_responses_from_file:
            self._load_raw_responses_from_file()

        if self.cache_settings.load_listings_from_file:
            self._load_listings_from_file()

        if self.cache_settings.pull_from_trade_api:
            self._pull_from_trade_api()
