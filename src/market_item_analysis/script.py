
from src.market_item_analysis.workflows.trade_api_results_ingestion import RawListingLoader
from src.market_item_analysis.core.input_output import IoManager
from src.market_item_analysis.trade_api import TradeApiInterface

io_manager = IoManager()
trade_api_handler = TradeApiInterface()

listings_loader = RawListingLoader(trade_api_handler=trade_api_handler,
                                   io_manager=io_manager)
listings_loader.pull_from_trade_api(pull_minutes_limit=60)

"""creator = TrainingDataCreator(io_manager=io_manager)
creator.create()"""
