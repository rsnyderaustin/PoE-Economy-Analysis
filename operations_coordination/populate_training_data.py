import random

import poecd_api
import psql
import trade_api
from data_handling import ListingBuilder
from data_transforming import ListingsTransforming
from shared import env_loading
from trade_api.query import QueryPresets


class TrainingDataPopulator:

    def __init__(self, refresh_poecd_source: bool, testing=False):
        self.trade_api_handler = trade_api.TradeApiHandler()

        global_atypes_manager = poecd_api.PoecdDataManager(refresh_data=refresh_poecd_source).build_global_mods_manager()
        self.listing_builder = ListingBuilder(global_atypes_manager)

        self.env_loader = env_loading.EnvLoader()
        self.psql_manager = psql.PostgreSqlManager(skip_sql=testing)

    def _process_and_insert(self, responses):
        listings = [self.listing_builder.build_listing(api_r) for api_r in responses]
        row_data = ListingsTransforming.to_flat_rows(listings)
        self.psql_manager.insert_data(
            table_name=self.env_loader.get_env("PSQL_TRAINING_TABLE"),
            data=row_data
        )

    def fill_training_data(self, api_item_responses: list[dict]):
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        if api_item_responses:
            self._process_and_insert(api_item_responses)
            return

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            self._process_and_insert(api_item_responses)