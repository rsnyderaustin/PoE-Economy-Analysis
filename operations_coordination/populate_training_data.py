import random
import datetime
import psutil
import os

import psql
import trade_api
from data_handling import ListingBuilder, ApiResponseParser
from data_transforming import ListingsTransforming
from file_management import Poe2DbModsManagerFile, RawListingsFile
from psql import PostgreSqlManager
from shared import env_loading
from shared.logging import LogsHandler, LogFile
from trade_api.query import QueryPresets

overview_log = LogsHandler().fetch_log(LogFile.PROGRAM_OVERVIEW)


class _ListingImportGatekeeper:

    def __init__(self, psql_manager: PostgreSqlManager):
        if psql_manager.skip_sql:
            self.keys = set()
            return

        dates_and_ids = psql_manager.fetch_columns_data(table_name='listings',
                                                        columns=['date_fetched', 'listing_id'])
        self.keys = {
            (listing_id, date_fetched)
            for listing_id, date_fetched in zip(dates_and_ids['listing_id'], dates_and_ids['date_fetched'])
        }

    def listing_is_valid(self, listing_id: str, date_fetched: datetime, register_if_valid=True) -> bool:
        is_valid = (listing_id, date_fetched) not in self.keys
        if not is_valid:
            return False

        if register_if_valid:
            self.register_listing(listing_id=listing_id, date_fetched=date_fetched)

        return True

    def register_listing(self, listing_id: str, date_fetched: datetime):
        self.keys.add((listing_id, date_fetched))



def _log_memory_usage(stage=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 ** 2)  # in MB
    print(f"[Memory] {stage}: {mem:.2f} MB")


class TrainingDataPopulator:

    def __init__(self,
                 psql_manager: psql.PostgreSqlManager):
        self.trade_api_handler = trade_api.TradeApiHandler(psql_manager=psql_manager)
        self.psql_manager = psql_manager

        self._poe2db_mods_manager = Poe2DbModsManagerFile().load(missing_ok=False)
        self.listing_builder = ListingBuilder(self._poe2db_mods_manager)

        self._listing_gatekeeper = _ListingImportGatekeeper(psql_manager=self.psql_manager)

        self.env_loader = env_loading.EnvLoader()

    def _process_and_insert(self, responses):
        listings = [self.listing_builder.build_listing(api_r) for api_r in responses]
        row_data = ListingsTransforming.to_flat_rows(listings)
        self.psql_manager.insert_data(
            table_name=self.env_loader.get_env("PSQL_TRAINING_TABLE"),
            data=row_data
        )

    def fill_training_data(self, raw_listings_file: RawListingsFile = None):
        program_start = datetime.datetime.now()
        print(f"fill_training_data start: {program_start}")
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        if raw_listings_file:
            for responses in raw_listings_file.load():
                parsers = [ApiResponseParser(response) for response in responses]
                valid_parsers = [rp for rp in parsers
                                 if self._listing_gatekeeper.listing_is_valid(listing_id=rp.listing_id,
                                                                              date_fetched=rp.date_fetched)]
                self._process_and_insert(valid_parsers)

        responses_fetched = 0
        for responses in self.trade_api_handler.fetch_responses(training_queries):
            parsers = [ApiResponseParser(response) for response in responses]
            valid_parsers = [rp for rp in parsers
                             if self._listing_gatekeeper.listing_is_valid(listing_id=rp.listing_id,
                                                                          date_fetched=rp.date_fetched)]

            raw_listings_data = [rp.raw_response_data for rp in valid_parsers]

            self._poe2db_mods_manager.save(raw_listings_data)

            _log_memory_usage()
            print(f"Fetched {len(valid_parsers)} API responses. Processing and inserting into PSQL.")
            responses_fetched += len(valid_parsers)

            self._process_and_insert(valid_parsers)

        print(f"fill_training_data fetched {responses_fetched} in "
              f"{(datetime.datetime.now() - program_start).seconds / 60} minutes.")
