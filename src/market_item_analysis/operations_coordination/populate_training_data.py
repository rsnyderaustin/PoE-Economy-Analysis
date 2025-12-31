import datetime
import os
import random
import logging

import psutil

from src.market_item_analysis import psql, trade_api
from src.market_item_analysis.core import env_loading
from src.market_item_analysis.data_handling import ListingBuilder, ApiResponseParser
from src.market_item_analysis.data_transforming import ListingsTransforming
from src.market_item_analysis.file_management.file_managers import RawListingsFile, PoE2EconomyAnalysisIOManager
from src.market_item_analysis.official_poe_api.api_response_parser import ApiResponse
from src.market_item_analysis.program_logging import LogsHandler, LogFile
from src.market_item_analysis.trade_api import ListingImportGatekeeper, TradeApiHandler
from src.market_item_analysis.trade_api.query import QueryPresets

logger = logging.getLogger(__name__)


def _log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # in MB
    print(f"[Memory] {stage}: {mem:.2f} MB")


class TrainingDataPopulator:

    def __init__(self,
                 trade_api_handler: TradeApiHandler,
                 listing_builder: ListingBuilder,
                 psql_manager: psql.PostgreSqlManager,
                 io_manager: PoE2EconomyAnalysisIOManager):
        self.trade_api_handler = trade_api_handler
        self.listing_builder = listing_builder
        self.psql_manager = psql_manager
        self.io_manager = io_manager

        self._listing_gatekeeper = ListingImportGatekeeper(psql_manager=self.psql_manager)
        self._raw_listings_file = RawListingsFile()

        self.env_loader = env_loading.EnvLoader()

    def _process_and_insert(self, api_responses: list[ApiResponse]):
        self.io_manager.save_raw_listings([r.to_dict() for r in api_responses])
        listings = [self.listing_builder.build_listing(api_r) for api_r in api_responses]
        self.io_manager.save_constructed_listings([l.to_dict() for l in listings])

        logger.info(f"Saved {len(listings)} listings to file.")

        row_data = ListingsTransforming.flatten(listings)
        self.psql_manager.insert_listing(
            table_name=self.env_loader.get_env("PSQL_TRAINING_TABLE"),
            data=row_data
        )

    def _pull_listings_from_file(self):


    def fill_training_data_from_listings_file(self, raw_listings_file: RawListingsFile):
        all_responses = 0
        valid_responses = 0
        for raw_response in raw_listings_file.load():
            all_responses += 1
            response = ApiResponse(raw_response)
            if not self._listing_gatekeeper.should_process_listing(listing_id=response.listing_id,
                                                                   date_fetched=response.date_fetched):
                continue

            listing = self.listing_builder.build_listing(response)

            valid_responses += 1
            self._process_and_insert(api_responses=[response])

            logger.info(f"JsonL Insert\nValid responses: {valid_responses}\nAll responses: {all_responses}")

    def fill_training_data(self):
        program_start = datetime.datetime.now()

        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        responses_fetched = 0
        for responses in self.trade_api_handler.fetch_responses(training_queries):
            self._raw_listings_file.save(responses)

            parsers = [ApiResponseParser(response) for response in responses]
            valid_parsers = [rp for rp in parsers
                             if self._listing_gatekeeper.should_process_listing(listing_id=rp.listing_id,
                                                                                date_fetched=rp.date_fetched)]

            _log_memory_usage()
            responses_fetched += len(valid_parsers)
            print(f"{len(valid_parsers)} valid API responses out of {len(parsers)} total API responses. "
                  f"Processing and inserting into PSQL.")

            self._process_and_insert(valid_parsers)

        print(f"fill_training_data fetched {responses_fetched} in "
              f"{(datetime.datetime.now() - program_start).seconds / 60} minutes.")
