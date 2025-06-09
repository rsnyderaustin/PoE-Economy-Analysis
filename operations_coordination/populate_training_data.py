import datetime
import os
import random

import psutil

import psql
import trade_api
from core import env_loading
from data_handling import ListingBuilder, ApiResponseParser
from data_transforming import ListingsTransforming
from file_management.file_managers import RawListingsFile, ListingStringsFile
from program_logging import LogsHandler, LogFile
from trade_api.listing_gatekeeper import ListingImportGatekeeper
from trade_api.query import QueryPresets

overview_log = LogsHandler().fetch_log(LogFile.PROGRAM_OVERVIEW)


def _log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # in MB
    print(f"[Memory] {stage}: {mem:.2f} MB")


class TrainingDataPopulator:

    def __init__(self,
                 listing_builder: ListingBuilder,
                 psql_manager: psql.PostgreSqlManager):
        self.trade_api_handler = trade_api.TradeApiHandler()
        self.psql_manager = psql_manager

        self.listing_builder = listing_builder

        self._listing_gatekeeper = ListingImportGatekeeper(psql_manager=self.psql_manager)
        self._raw_listings_file = RawListingsFile()

        self.env_loader = env_loading.EnvLoader()

    def _process_and_insert(self, responses: list[ApiResponseParser]):
        listings = [self.listing_builder.build_listing(api_r) for api_r in responses]

        for listing in listings:
            self.psql_manager.insert_listing_string(table_name='listing_strings',
                                                    my_id=listing.my_id,
                                                    listing_str=str(listing)
                                                    )

        overview_log.info(f"Inserted {len(listings)} listing strings into Psql.")

        row_data = ListingsTransforming.to_flat_rows(listings)
        self.psql_manager.insert_listing(
            table_name=self.env_loader.get_env("PSQL_TRAINING_TABLE"),
            data=row_data
        )

    def fill_training_data_from_listings_file(self, raw_listings_file: RawListingsFile):
        all_responses = 0
        valid_responses = 0
        for response in raw_listings_file.load():
            all_responses += 1
            parser = ApiResponseParser(response)
            if not self._listing_gatekeeper.listing_is_valid(listing_id=parser.listing_id,
                                                             date_fetched=parser.date_fetched):
                continue

            valid_responses += 1
            self._process_and_insert(responses=[parser])

            overview_log.info(f"JsonL Insert\nValid responses: {valid_responses}\nAll responses: {all_responses}")

    def fill_training_data(self):
        program_start = datetime.datetime.now()

        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        responses_fetched = 0
        for responses in self.trade_api_handler.fetch_responses(training_queries):
            self._raw_listings_file.save(responses)

            parsers = [ApiResponseParser(response) for response in responses]
            valid_parsers = [rp for rp in parsers
                             if self._listing_gatekeeper.listing_is_valid(listing_id=rp.listing_id,
                                                                          date_fetched=rp.date_fetched)]

            _log_memory_usage()
            responses_fetched += len(valid_parsers)
            print(f"{len(valid_parsers)} valid API responses out of {len(parsers)} total API responses. "
                  f"Processing and inserting into PSQL.")

            self._process_and_insert(valid_parsers)

        print(f"fill_training_data fetched {responses_fetched} in "
              f"{(datetime.datetime.now() - program_start).seconds / 60} minutes.")
