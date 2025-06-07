import random

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

from data_handling import ListingBuilder, ApiResponseParser
from file_management.file_managers import CraftingSimulatorFiles
from instances_and_definitions import ModifiableListing
from price_predict_ai_model import PricePredictor
from program_logging import LogsHandler, LogFile, log_errors
from trade_api import TradeApiHandler
from trade_api.query import QueryPresets
from .environment import CraftingEnvironment

craft_log = LogsHandler().fetch_log(LogFile.CRAFTING_MODEL)


class CraftingModelPipeline:
    
    def __init__(self,
                 trade_api_handler: TradeApiHandler,
                 listing_builder: ListingBuilder,
                 training_divs_budget: int,
                 total_timesteps: int = 10000):
        self._trade_api_handler = trade_api_handler
        self._listing_builder = listing_builder

        self._divs_budget = training_divs_budget
        self._total_timesteps = total_timesteps

        self._model_files = CraftingSimulatorFiles()

    def run(self):
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)
        for responses in self._trade_api_handler.fetch_responses(training_queries):
            parsers = [ApiResponseParser(response) for response in responses]
            listings = [self._listing_builder.build_listing(rp) for rp in parsers]

            if not listings:
                continue

            for listing in listings:
                self._train_crafting_model(listing=listing)


    @log_errors(craft_log)
    def _train_crafting_model(self, listing: ModifiableListing):
        price_predict_model = self._model_files.load_model(atype=listing.item_atype)
        if not price_predict_model:
            raise ValueError(f"PricePredictModel for Atype {listing.item_atype} does not exist.")

        price_predictor = PricePredictor(price_predict_model)

        env = CraftingEnvironment(listing=listing,
                                  divs_budget=self._divs_budget,
                                  price_predictor=price_predictor)

        check_env(env)

        model = self._model_files.load_model(listing.item_atype)
        if not model:
            model = PPO("MlpPolicy", env=env)

        model.set_env(env)
        model.learn(total_timesteps=self._total_timesteps)

        self._model_files.save_model(atype=listing.item_atype, model=model)
