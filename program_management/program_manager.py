
import configparser
import logging
import random

import xgboost as xgb

import price_predict_model
import data_ingestion
from price_predict_model.build_model import build_price_predict_model
import trade_api
from trade_api import query
from data_synthesizing.poecd_data_injector import PoecdDataInjector
from file_management import FilesManager, FileKey

logging.basicConfig(level=logging.INFO,
                    force=True)

config = configparser.ConfigParser


class ProgramManager:

    def __init__(self):
        logging.info("Initializing ProgramManager.")
        self.trade_api_handler = trade_api.TradeApiHandler()
        self.files_manager = FilesManager()
        self.mods_handler = data_handling.ModsHandler()
        self.injector = PoecdDataInjector()
        self.price_predict_data_manager = price_predict_model.PricePredictDataManager()
        logging.info("Finished initializing ProgramManager.")

    def fetch_training_data(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        while True:
            for i, api_item_responses in enumerate(self.trade_api_handler.process_queries(training_queries)):

                listings = []
                for api_item_response in api_item_responses:
                    listing = data_ingestion.create_listing(api_item_response)
                    listings.append(listing)

                    for mod in listing.mods:

                        self.injector.inject_poecd_data_into_mod(item_mod=mod)
                        self.files_manager.cache_mod(item_mod=mod)

                self.price_predict_data_manager.cache_training_data(listings)

                if i % 5 == 0:
                    self.files_manager.save_data()

    def find_underpriced_items(self):
        training_queries = query.QueryPresets().training_fills
        predict_model = self.files_manager.file_data[FileKey.PRICE_PREDICT_MODEL]

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            self.files_manager.file_data[FileKey.MARKET_SCAN] = {
                col: [] for col in self.files_manager.file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING].keys()
            }

            listings = [data_ingestion.create_listing(api_item_response) for api_item_response in api_item_responses]

            self.price_predict_data_manager.cache_market_data(listings)
            df = self.price_predict_data_manager.export_data_for_model(which_file=FileKey.MARKET_SCAN)
            true_prices = list(df['exalts'])
            df.drop(columns=['exalts'], inplace=True)

            df = df[predict_model.feature_names]
            dmatrix = xgb.DMatrix(df)
            predicts = predict_model.predict(dmatrix)

            df['true_exalts'] = true_prices
            df['predicted_exalts'] = predicts

    def build_price_predict_model(self):
        model_data = self.price_predict_data_manager.export_data_for_model(which_file=FileKey.CRITICAL_PRICE_PREDICT_TRAINING)
        model = build_price_predict_model(df=model_data)
        self.files_manager.file_data[FileKey.PRICE_PREDICT_MODEL] = model
        self.files_manager.save_data(keys=[FileKey.PRICE_PREDICT_MODEL])

