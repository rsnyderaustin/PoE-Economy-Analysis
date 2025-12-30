from src.market_item_analysis import psql
from src.market_item_analysis.crafting_ai_model import CraftingModelPipeline
from src.market_item_analysis.data_handling import ListingBuilder
from src.market_item_analysis.file_management.file_managers import Poe2DbModsManagerFile
from trade_api import TradeApiHandler

poe2db_mods_manager = Poe2DbModsManagerFile().load(missing_ok=False)

psql_manager = psql.PostgreSqlManager()
trade_api_handler = TradeApiHandler(psql_manager)

listing_builder = ListingBuilder(poe2db_mods_manager)

crafting_pipeline = CraftingModelPipeline(poe2db_mods_manager=poe2db_mods_manager,
                                          trade_api_handler=trade_api_handler,
                                          listing_builder=listing_builder,
                                          training_divs_budget=100)
crafting_pipeline.run()

