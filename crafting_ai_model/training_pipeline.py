import random

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

from file_management import FilesManager, ModelPath
from instances_and_definitions import ModifiableListing
from price_predict_ai_model import PricePredictor
from trade_api import TradeApiHandler
from trade_api.query import QueryPresets
from .environment import CraftingEnvironment
from data_handling import ListingBuilder


class CraftingModelPipeline:
    
    def __init__(self,
                 files_manager: FilesManager,
                 trade_api_handler: TradeApiHandler,
                 listing_builder: ListingBuilder,
                 training_exalts_budget: int,
                 total_timesteps: int = 10000):
        self._files_manager = files_manager
        self._trade_api_handler = trade_api_handler
        self._listing_builder = listing_builder

        self._exalts_budget = training_exalts_budget
        self._total_timesteps = total_timesteps

        self._loaded_models = dict()

    def run(self):
        training_queries = QueryPresets().training_fills
        random.shuffle(training_queries)
        for api_item_responses in self._trade_api_handler.process_queries(training_queries):
            listings = [self._listing_builder.build_listing(api_r) for api_r in api_item_responses]

            if not listings:
                continue

            for listing in listings:
                self._train_crafting_model(listing=listing)

    def _train_crafting_model(self, listing: ModifiableListing):
        price_predict_model = self._files_manager.load_price_predict_model(atype=listing.item_atype)
        if not price_predict_model:
            raise ValueError(f"PricePredictModel for Atype {listing.item_atype} does not exist.")

        price_predictor = PricePredictor(price_predict_model)

        env = CraftingEnvironment(listing=listing,
                                  exalts_budget=self._exalts_budget,
                                  price_predictor=price_predictor)

        check_env(env)

        if listing.item_atype in self._loaded_models:
            craft_model = self._loaded_models[listing.item_atype]
        else:
            craft_model = self._files_manager.load_crafting_model(atype=listing.item_atype)

            if not craft_model:
                craft_model = PPO("MlpPolicy", env=env)

            self._loaded_models[listing.item_atype] = craft_model

        craft_model.set_env(env)
        craft_model.learn(total_timesteps=self._total_timesteps)
