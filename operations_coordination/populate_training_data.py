import random

from poecd_api import PoecdDataManager
import psql
import trade_api
from data_handling import ListingBuilder
from data_transforming import ListingsTransforming
from file_management import FilesManager, DataPath
from shared import env_loading
from trade_api.query import QueryPresets


class TrainingDataPopulator:

    def __init__(self, files_manager: FilesManager, refresh_poecd_source: bool, testing=False):
        self.trade_api_handler = trade_api.TradeApiHandler()

        if refresh_poecd_source or not files_manager.file_data[DataPath.GLOBAL_POECD_MANAGER]:
            global_atypes_manager = PoecdDataManager(refresh_data=refresh_poecd_source).build_global_mods_manager()
            files_manager.file_data[DataPath.GLOBAL_POECD_MANAGER] = global_atypes_manager
            files_manager.save_data([DataPath.GLOBAL_POECD_MANAGER])

        global_atypes_manager = files_manager.file_data[DataPath.GLOBAL_POECD_MANAGER]
        if not global_atypes_manager:
            global_atypes_manager = PoecdDataManager(refresh_data=refresh_poecd_source).build_global_mods_manager()

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

    def fill_training_data(self, api_item_responses: list[dict]=None):
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)

        if api_item_responses:
            self._process_and_insert(api_item_responses)
            return

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            self._process_and_insert(api_item_responses)
