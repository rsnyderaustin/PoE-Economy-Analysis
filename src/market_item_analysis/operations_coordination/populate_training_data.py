import datetime
import os
import logging

import psutil

from src.market_item_analysis import psql
from src.market_item_analysis.file_management import logging_setup
from src.market_item_analysis.instances_and_definitions.item_instances import EquipmentListing
from src.market_item_analysis.operations_coordination.cache_settings import CacheSettings
from src.market_item_analysis.data_handling import ListingBuilder, ApiResponseParser
from src.market_item_analysis.file_management.io_manager import PoE2EconomyAnalysisIOManager
from src.market_item_analysis.trade_api.api_response_obj import ApiResponse
from src.market_item_analysis.trade_api import TradeApiHandler
from src.market_item_analysis.trade_api.query import QueryPresets

logger = logging.getLogger(__name__)


def _log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # in MB
    print(f"[Memory] {stage}: {mem:.2f} MB")


class _ListingResults:

    def __init__(self):
        self.num_responses = 0
        self.num_valid_listings = 0


class _ListingsFactory:

    def __init__(self, existing_listings: list[EquipmentListing]):
        sorted_listings = sorted(existing_listings, key=lambda l: l.metadata.date_fetched)
        self._date_fetched_d = {listing.metadata.listing_id: listing.metadata.date_fetched
                                for listing in sorted_listings}

    def _filter_redundant_api_responses(self, api_responses: list[ApiResponse]) -> list[ApiResponse]:
        valid_api_responses = []
        for api_response in api_responses:
            if (api_response.listing_id in self._responses_d
                and api_response.date_fetched < self._responses_d[api_response.listing_id]):
                continue

            self._responses_d[api_response.listing_id] = api_response.date_fetched
            valid_api_responses.append(api_response)

        return valid_api_responses

    def create_listings(self,
                        raw_api_responses: list[dict],
                        filter_out_old_listings: bool) -> list[EquipmentListing]:
        api_responses = [ApiResponse(raw_api_response) for raw_api_response in raw_api_responses]

        if filter_out_old_listings:
            api_responses = self._filter_redundant_api_responses(api_responses=api_responses)

        listings = []
        for api_response in api_responses:
            listing = ListingBuilder.build_listing(api_response)

            if not self._listing_gatekeeper.should_process_listing(listing=listing):
                continue

            listings.append(listing)

        return listings


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

    def populate(self):
        if self.cache_settings.load_raw_api_responses:
            raw_api_responses = self.io_manager.load_raw_listings()
            listings = _ListingsFactory()

    def fill_training_data_from_listings_file(self):
        logger.info("\nfill_training_data_from_listings_file()")

        raw_api_responses = self.io_manager.load_raw_listings()
        listings = self._create_listings(raw_api_responses=raw_api_responses,
                                         filter_out_old_listings=True)

        logger.info(
            f"\tLoaded {len(raw_api_responses)} raw API responses from file."
            f"\n\tCreated {len(listings)} valid listings"
        )

    def fill_training_data_from_trade_api(self):
        logger.info("\nfill_training_data_from_trade_api()")

        training_queries = QueryPresets.create_training_data_queries().shuffle().queries

        results = _ListingResults()
        for i, responses in enumerate(self.trade_api_handler.fetch_responses(training_queries)):
            results.num_responses += len(responses)
            self._raw_listings_file.save(responses)

            listings = _ListingsFactory.create_listings(raw_api_responses=responses,
                                                        filter_out_old_listings=True)
            listings = self._create_listings(raw_api_responses=responses, fil)
            results.num_valid_listings += len(listings)
            parsers = [ApiResponseParser(response) for response in responses]
            valid_parsers = [rp for rp in parsers
                             if self._listing_gatekeeper.should_process_listing(listing_id=rp.listing_id,
                                                                                date_fetched=rp.date_fetched)]

            print(
                "\nfill_training_data_from_trade_api()"
                f"\n\tIteration {i}:"
                f"\n\tAPI responses: {len(valid_parsers)}"
                f"\n\tValid listings created: {len(listings)}"
                f"\n\tTotal:"
                f"\n\tAPI responses: {results.num_responses}"
                f"\n\tValid listings created: {results.num_valid_listings}"
            )

            self._process_and_insert(valid_parsers)

        print(f"fill_training_data fetched {responses_fetched} in "
              f"{(datetime.datetime.now() - program_start).seconds / 60} minutes.")
