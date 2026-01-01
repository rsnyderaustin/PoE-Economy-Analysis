
from src.market_item_analysis.program_processes.raw_listings_loader import RawListingLoader
from src.market_item_analysis.program_processes.create_training_data import TrainingDataCreator
from src.market_item_analysis.shared.io_manager import IoManager
from src.market_item_analysis.trade_api import TradeApiHandler

io_manager = IoManager()
trade_api_handler = TradeApiHandler()

listings_loader = RawListingLoader(trade_api_handler=trade_api_handler,
                                   io_manager=io_manager)
listings_loader.pull_from_trade_api(pull_minutes_limit=1)

"""creator = TrainingDataCreator(io_manager=io_manager)
creator.create()"""
