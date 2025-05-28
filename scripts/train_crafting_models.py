
from crafting_ai_model import CraftingModelPipeline
from data_handling import ListingBuilder
from file_management import FilesManager
from poecd_api import PoecdDataManager
from trade_api import TradeApiHandler

files_manager = FilesManager()

trade_api_handler = TradeApiHandler()

global_atypes_manager = PoecdDataManager(refresh_data=True).build_global_mods_manager()
listing_builder = ListingBuilder(global_atypes_manager)

crafting_pipeline = CraftingModelPipeline(files_manager=files_manager,
                                          trade_api_handler=trade_api_handler,
                                          listing_builder=listing_builder,
                                          training_divs_budget=100)
crafting_pipeline.run()

