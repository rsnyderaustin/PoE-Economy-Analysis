import psql
from crafting_ai_model import CraftingModelPipeline
from data_handling import ListingBuilder
from file_management import FilesManager, DataPath
from trade_api import TradeApiHandler

fm = FilesManager()
poe2db_mods_manager = fm.fetch_data(data_path_e=DataPath.POE2DB_MODS, missing_ok=False)

psql_manager = psql.PostgreSqlManager()
trade_api_handler = TradeApiHandler(psql_manager)

listing_builder = ListingBuilder(poe2db_mods_manager)

crafting_pipeline = CraftingModelPipeline(files_manager=fm,
                                          trade_api_handler=trade_api_handler,
                                          listing_builder=listing_builder,
                                          training_divs_budget=100)
crafting_pipeline.run()

