import random

import psql
import trade_api
from data_handling import ListingBuilder
from data_transforming import ListingsTransforming
from file_management import FilesManager, DataPath
from shared import env_loading
from trade_api.query import QueryPresets


class TrainingDataPopulator:

    def __init__(self,
                 files_manager: FilesManager,
                 psql_manager: psql.PostgreSqlManager):
        self.trade_api_handler = trade_api.TradeApiHandler(psql_manager=psql_manager)
        self.psql_manager = psql_manager

        # Technically we don't need to have the Poe2Db mods manager if we have full coverage of all mods
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

    def fill_training_data(self, api_item_responses: list[dict]=None):
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        if api_item_responses:
            self._process_and_insert(api_item_responses)
            return

        for api_item_responses in self.trade_api_handler.generate_responses_from_queries(training_queries):
            self._process_and_insert(api_item_responses)
