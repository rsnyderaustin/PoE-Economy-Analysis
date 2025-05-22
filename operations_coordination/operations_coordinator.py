
import configparser
import logging
import random

import xgboost as xgb

import crafting_ai_model
import data_handling
import data_transforming
import poecd_api
import price_predict_ai_model
import psql
import trade_api
from file_management import FilesManager, ModelPath
from instances_and_definitions import ModifiableListing
from price_predict_ai_model.build_model import build_price_predict_model
from shared import shared_utils, env_loader, env_loading
from stat_analysis.stats_prep import StatsPrep
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

        self.env_loader = env_loading.EnvLoader()
        self.psql_manager = psql.PostgreSqlManager()
        logging.info("Finished initializing ProgramManager.")

    def _create_listings(self, api_item_responses) -> list[ModifiableListing]:
        listings = []

        for api_item_response in api_item_responses:
            mods = self.resource_resolver.process_mods(item_data=api_item_response['item'])
            listing = data_handling.ListingFactory.create_listing(api_item_response=api_item_response,
                                                                  item_mods=mods)
            listings.append(listing)

        return listings

    def fill_training_data(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = self._create_listings(api_item_responses)
            row_data = data_transforming.ListingsTransforming.to_flat_rows(listings)
            self.psql_manager.insert_data(table_name=self.env_loader.get_env("PSQL_TRAINING_TABLE"),
                                          data=row_data)

    def find_underpriced_items(self):
        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        if not self.files_manager.has_data(ModelPath.PRICE_PREDICT_MODEL):
            raise ValueError("Called train_crafting_model when there is no price predict model stored.")

        predict_model = self.files_manager.model_data[ModelPath.PRICE_PREDICT_MODEL]

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = self._create_listings(api_item_responses)
            listings_df = data_transforming.ListingsTransforming.to_price_predict_df(listings)

            prices = list(listings_df['exalts'])
            listings_df = listings_df.drop(columns=['exalts'])

            listings_df = listings_df[predict_model.feature_names]
            dmatrix = xgb.DMatrix(listings_df, enable_categorical=True)
            predicts = predict_model.predict(dmatrix)

            listings_df['true_exalts'] = prices
            listings_df['predicted_exalts'] = predicts

            listings_df['predict_portion'] = listings_df['predicted_exalts'] / listings_df['true_exalts']

            underpriced_df = listings_df[listings_df['predict_portion'] < 0.8]
            underpriced_items = underpriced_df.to_dict(orient='records')
            for item in underpriced_items:
                shared_utils.log_dict(item)

    def build_price_predict_model(self):
        psql_table_name = env_loader.get_env("PSQL_TRAINING_TABLE")
        training_data = self.psql_manager.fetch_table_data(psql_table_name)
        model_df = data_transforming.ListingsTransforming.to_price_predict_df(rows=training_data)

        atypes = model_df['atype'].unique()
        for atype in atypes:
            atype_df = model_df[model_df['atype'] == atype]
            logging.info(f"Prepping model data for Atype {atype}")
            atype_df = StatsPrep.prep_data(df=atype_df, atype=atype, price_column='exalts')

            if atype_df is None:  # This only happens if no column in the atype_df has enough of a correlation
                continue

            logging.info(f"Building model for Atype {atype}")
            model = build_price_predict_model(df=atype_df, atype=str(atype), price_column='exalts')
            self.files_manager.model_data[ModelPath.PRICE_PREDICT_MODEL] = model
            self.files_manager.save_data(paths=[ModelPath.PRICE_PREDICT_MODEL])

    def train_crafting_model(self):
        craft_model = self.files_manager.model_data[ModelPath.CRAFTING_MODEL]
        if not self.files_manager.has_data(ModelPath.PRICE_PREDICT_MODEL):
            raise ValueError("Called train_crafting_model when there is no price predict model stored.")

        price_predict_model = self.files_manager.model_data[ModelPath.PRICE_PREDICT_MODEL]

        training_queries = query.QueryPresets().training_fills
        random.shuffle(training_queries)

        for api_item_responses in self.trade_api_handler.process_queries(training_queries):
            listings = self._create_listings(api_item_responses)

            for listing in listings:
                crafting_ai_model.RlTrainer.train(
                    listing=listing,
                    price_predictor_model=price_predict_model,
                    crafting_model=craft_model
                )

            self.files_manager.save_data(paths=[ModelPath.CRAFTING_MODEL])
