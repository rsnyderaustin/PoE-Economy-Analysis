
import configparser
import logging
import random

import xgboost as xgb

import data_handling
import poecd_api
import price_predict_model
import trade_api
from file_management import FilesManager, FileKey
from price_predict_model.build_model import build_price_predict_model
from stat_analysis.stats_prep import StatsPrep
from shared import shared_utils
from trade_api import query

logging.basicConfig(level=logging.INFO,
                    force=True)

config = configparser.ConfigParser


class OperationsCoordinator:

    def __init__(self, refresh_poecd_source: bool = False):
        logging.info("Initializing ProgramManager.")
        self.trade_api_handler = trade_api.TradeApiHandler()
        self.files_manager = FilesManager()

        global_atypes_manager = poecd_api.PoecdManager(refresh_data=refresh_poecd_source).create_global_atypes_manager()
        self.resource_resolver = data_handling.ModResolver(global_atypes_manager=global_atypes_manager)

        self.price_predict_data_manager = price_predict_model.PricePredictDataManager()
        logging.info("Finished initializing ProgramManager.")

    def fill_training_data(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        while True:
            for i, api_item_responses in enumerate(self.trade_api_handler.process_queries(training_queries)):
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
        random.shuffle(training_queries)

        predict_model = self.files_manager.model_data[FileKey.PRICE_PREDICT_MODEL]

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = []
            for api_item_response in api_item_responses:
                mods = self.resource_resolver.pull_mods(item_data=api_item_response['item'])
                listing = data_handling.ListingFactory.create_listing(
                    api_item_response=api_item_response,
                    item_mods=mods
                )
                listings.append(listing)

            listing_account_names = [listing.account_name for listing in listings]
            self.price_predict_data_manager.cache_market_data(listings)
            market_df = self.price_predict_data_manager.export_data_for_model(which_file=FileKey.MARKET_SCAN)
            listing_prices = list(market_df['exalts'])
            market_df.drop(columns=['exalts'], inplace=True)

            market_df = market_df[predict_model.feature_names]
            dmatrix = xgb.DMatrix(market_df, enable_categorical=True)
            predicts = predict_model.predict(dmatrix)

            market_df['true_exalts'] = listing_prices
            market_df['predicted_exalts'] = predicts
            market_df['account_name'] = listing_account_names

            underpriced_items_df = market_df[market_df['predicted_exalts'] > market_df['true_exalts']]
            underpriced_items = underpriced_items_df.to_dict(orient='records')
            for item in underpriced_items:
                shared_utils.log_dict(item)

            self.price_predict_data_manager.clear_market_cache()

    def build_price_predict_model(self):
        model_df = self.price_predict_data_manager.export_data_for_model(which_file=FileKey.CRITICAL_PRICE_PREDICT_TRAINING)

        atype_dfs = {
            atype: atype_df
            for atype, atype_df in model_df.groupby('atype')
        }
        atype_dfs = {
            atype: StatsPrep(df=atype_df.reset_index(drop=True), atype=str(atype), price_column='exalts').prep_data()
            for atype, atype_df in atype_dfs.items()
        }

        for atype, atype_df in atype_dfs.items():
            logging.info(f"Building model for Atype {atype}")
            model = build_price_predict_model(df=atype_df, atype=str(atype))
            self.files_manager.model_data[FileKey.PRICE_PREDICT_MODEL] = model
            self.files_manager.save_model(model_key=FileKey.PRICE_PREDICT_MODEL)

