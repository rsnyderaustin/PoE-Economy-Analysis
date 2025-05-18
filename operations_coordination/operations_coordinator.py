
import configparser
import logging
import random
import time

import xgboost as xgb

import data_handling
import poecd_api
import price_predict_model
import trade_api
from file_management import FilesManager, FileKey
from price_predict_model.build_model import build_price_predict_model
from stat_analysis.stats_prep import StatsPrep
from shared import shared_utils, env_loader, env_loading, EnvVariable
from trade_api import query
import psql

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

        self.price_predict_data_manager = price_predict_model.ListingsDataProcessor()

        self.env_loader = env_loading.EnvLoader()
        self.psql_manager = psql.PostgreSqlManager()
        logging.info("Finished initializing ProgramManager.")

    def fill_training_data(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        while True:
            try:
                for api_item_responses in self.trade_api_handler.process_queries(training_queries):
                    listings = []
                    for api_item_response in api_item_responses:

                        mods = self.resource_resolver.process_mods(item_data=api_item_response['item'])
                        listing = data_handling.ListingFactory.create_listing(api_item_response=api_item_response,
                                                                              item_mods=mods)
                        listings.append(listing)

                    flattened_data = self.price_predict_data_manager.flatten_listings_into_dict(listings)

                    self.psql_manager.insert_data(table_name=self.env_loader.get_env(env_loading.EnvVariable.PSQL_TRAINING_TABLE),
                                                  data=flattened_data)
            except Exception as e:
                logging.error(f"Error in fill_training_data: {e}")
                time.sleep(env_loader.get_env(EnvVariable.RETRY_SEC_DELAY.value))

    def find_underpriced_items(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        predict_model = self.files_manager.model_data[FileKey.PRICE_PREDICT_MODEL]

        if not predict_model:
            raise ValueError(f"Predict model is unexpectedly None.")

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = []
            for api_item_response in api_item_responses:
                mods = self.resource_resolver.process_mods(item_data=api_item_response['item'])
                listing = data_handling.ListingFactory.create_listing(api_item_response=api_item_response,
                                                                      item_mods=mods)
                listings.append(listing)
            flattened_data = self.price_predict_data_manager.flatten_listings_into_dict(listings)
            model_df = self.price_predict_data_manager.prepare_flattened_listings_data_for_model(flattened_data)
            prices = list(model_df['exalts'])
            model_df = model_df.drop(columns=['exalts'])

            model_df = model_df[predict_model.feature_names]
            dmatrix = xgb.DMatrix(model_df, enable_categorical=True)
            predicts = predict_model.predict(dmatrix)

            model_df['true_exalts'] = prices
            model_df['predicted_exalts'] = predicts

            model_df['predict_portion'] = model_df['predicted_exalts'] / model_df['true_exalts']

            underpriced_df = model_df[model_df['predict_portion'] < 0.8]
            underpriced_items = underpriced_df.to_dict(orient='records')
            for item in underpriced_items:
                shared_utils.log_dict(item)

    def build_price_predict_model(self):
        psql_table_name = env_loader.get_env(EnvVariable.PSQL_TRAINING_TABLE)
        training_data = self.psql_manager.fetch_table_data(psql_table_name)
        model_df = self.price_predict_data_manager.prepare_flattened_listings_data_for_model(training_data)

        atypes = model_df['atype'].unique()
        for atype in atypes:
            atype_df = model_df[model_df['atype'] == atype]
            logging.info(f"Prepping model data for Atype {atype}")
            atype_df = StatsPrep.prep_data(df=atype_df, atype=atype, price_column='exalts')

            if atype_df is None:  # This only happens if no column in the atype_df has enough of a correlation
                continue

            logging.info(f"Building model for Atype {atype}")
            model = build_price_predict_model(df=atype_df, atype=str(atype), price_column='exalts')
            self.files_manager.save_model(model=model,
                                          model_key=FileKey.PRICE_PREDICT_MODEL)

