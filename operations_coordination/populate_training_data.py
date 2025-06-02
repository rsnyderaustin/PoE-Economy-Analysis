import random
import datetime
import psutil
import os

import psql
import trade_api
from data_handling import ListingBuilder
from data_transforming import ListingsTransforming
from file_management import FilesManager, DataPath
from shared import env_loading
from shared.logging import LogsHandler, LogFile
from trade_api.query import QueryPresets

overview_log = LogsHandler().fetch_log(LogFile.PROGRAM_OVERVIEW)

def _log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # in MB
    print(f"[Memory] {stage}: {mem:.2f} MB")

class TrainingDataPopulator:

    def __init__(self,
                 files_manager: FilesManager,
                 psql_manager: psql.PostgreSqlManager):
        self.trade_api_handler = trade_api.TradeApiHandler(psql_manager=psql_manager)
        self.psql_manager = psql_manager

        self.files_manager = FilesManager()
        poe2db_mods_manager = files_manager.fetch_data(DataPath.POE2DB_MODS_MANAGER, default=dict())
        self.listing_builder = ListingBuilder(poe2db_mods_manager)

        self.env_loader = env_loading.EnvLoader()

    def _process_and_insert(self, responses):
        listings = [self.listing_builder.build_listing(api_r) for api_r in responses]
        row_data = ListingsTransforming.to_flat_rows(listings)
        self.psql_manager.insert_data(
            table_name=self.env_loader.get_env("PSQL_TRAINING_TABLE"),
            data=row_data
        )

    def fill_training_data(self):
        program_start = datetime.datetime.now()
        print(f"fill_training_data start: {program_start}")
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        responses_fetched = 0
        for response_parsers in self.trade_api_handler.generate_responses_from_queries(training_queries):
            raw_listings_data = [rp.raw_response_data for rp in response_parsers]
            self.files_manager.append_json_list(path=DataPath.RAW_LISTINGS, records=raw_listings_data)

            _log_memory_usage()
            print(f"Fetched {len(response_parsers)} API responses. Processing and inserting into PSQL.")
            responses_fetched += len(response_parsers)

            self._process_and_insert(response_parsers)

        print(f"fill_training_data fetched {responses_fetched} in "
              f"{(datetime.datetime.now() - program_start).seconds / 60} minutes.")
