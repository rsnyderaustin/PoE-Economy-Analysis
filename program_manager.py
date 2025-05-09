
import configparser
import itertools
import logging

import data_ingestion
from file_management import FilesManager, FileKey
from data_ingestion import trade_api
from data_synthesizing.poecd_data_injecter import PoecdDataInjecter
from shared import trade_item_enums
from data_ingestion.trade_api import query
from ai_models import DataIngester
from ai_models.build_model import build_price_predict_model
from ai_models import data_prep

logging.basicConfig(level=logging.INFO,
                    force=True)

config = configparser.ConfigParser


class ProgramManager:

    def __init__(self):
        self.trade_api_handler = trade_api.TradeApiHandler()
        self.files_manager = FilesManager()
        self.injector = PoecdDataInjecter()
        self.ai_data_prep = DataPrep()

    def load_training_data(self):
        training_queries = query.QueryPresets().training_fills

        for i, api_item_responses in enumerate(self.trade_api_handler.process_queries(training_queries)):

            listings = []
            for api_item_response in api_item_responses:
                listing = data_ingestion.create_listing(api_item_response)
                listings.append(listing)

                for mod in listing.mods:
                    self.injector.inject_poecd_data_into_mod(item_mod=mod)
                    self.files_manager.cache_mod(item_mod=mod)

            logging.info(f"Caching and saving {len(listings)} listings.")
            self.files_manager.cache_listings_attributes(listings=listings)

            self.ai_data_prep.save_training_data(listings)

            if i % 5 == 0:
                self.files_manager.save_data()

    def find_underpriced_items(self):
        training_queries = query.QueryPresets().training_fills
        predict_model = self.files_manager.file_data[FileKey.PRICE_PREDICT_MODEL]

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = []
            for api_item_response in api_item_responses:
                listing = data_ingestion.create_listing(api_item_response)
                listings.append(listing)


    @staticmethod
    def build_price_predict_model():
        build_price_predict_model()

