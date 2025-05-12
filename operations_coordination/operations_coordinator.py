
import configparser
import logging
import random

import xgboost as xgb

import data_handling
import price_predict_model
from price_predict_model.build_model import build_price_predict_model
import poecd_api
import trade_api
from trade_api import query
from file_management import FilesManager, FileKey

logging.basicConfig(level=logging.INFO,
                    force=True)

config = configparser.ConfigParser


class OperationsCoordinator:

    def __init__(self):
        logging.info("Initializing ProgramManager.")
        self.trade_api_handler = trade_api.TradeApiHandler()
        self.files_manager = FilesManager()

        global_atypes_manager = poecd_api.PoecdManager(refresh_data=True).create_global_atypes_manager()
        self.resource_resolver = data_handling.ModResolver(global_atypes_manager=global_atypes_manager)

        self.price_predict_data_manager = price_predict_model.PricePredictDataManager()
        logging.info("Finished initializing ProgramManager.")

    def fill_training_data(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        while True:
            for i, api_item_responses in enumerate(self.trade_api_handler.process_queries(training_queries)):
                logging.info(f"Pulled {len(api_item_responses)} API item responses.")
                listings = []
                for api_item_response in api_item_responses:
                    mods = self.resource_resolver.pull_mods(item_data=api_item_response['item'])
                    listing = data_handling.ListingFactory.create_listing(api_item_response=api_item_response,
                                                                          item_mods=mods)
                    listings.append(listing)

                self.price_predict_data_manager.cache_training_data(listings)

                if i % 5 == 0:
                    self.files_manager.save_data()

    def find_underpriced_items(self):
        training_queries = query.QueryPresets().training_fills
        predict_model = self.files_manager.file_data[FileKey.PRICE_PREDICT_MODEL]

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = []
            for api_item_response in api_item_responses:
                mods = self.resource_resolver.pull_mods(item_data=api_item_response['item'])
                listing = data_handling.ListingFactory.create_listing(
                    api_item_response=api_item_response,
                    item_mods=mods
                )
                listings.append(listing)

            self.price_predict_data_manager.cache_market_data(listings)
            market_df = self.price_predict_data_manager.export_data_for_model(which_file=FileKey.MARKET_SCAN)
            true_prices = list(market_df['exalts'])
            market_df.drop(columns=['exalts'], inplace=True)

            market_df = market_df[predict_model.feature_names]
            dmatrix = xgb.DMatrix(market_df)
            predicts = predict_model.predict(dmatrix)

            market_df['true_exalts'] = true_prices
            market_df['predicted_exalts'] = predicts

    def build_price_predict_model(self):
        model_data = self.price_predict_data_manager.export_data_for_model(which_file=FileKey.CRITICAL_PRICE_PREDICT_TRAINING)
        model = build_price_predict_model(df=model_data)
        self.files_manager.file_data[FileKey.PRICE_PREDICT_MODEL] = model
        self.files_manager.save_data(keys=[FileKey.PRICE_PREDICT_MODEL])

