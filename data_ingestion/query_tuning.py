

import logging
import itertools

import data_ingestion
import external_apis
from data_exporting import ExportManager
from data_synthesizing.poecd_data_injecter import PoecdDataInjecter
from external_apis import ItemCategory, ListedSince
from shared import ATypeClassifier
from xgboost_model import DataPrep


import external_apis.trade_api

def _apply_create_listing_id_history(row, listing_id_history: dict):
    listing_id = row['listing_id']
    listing_date = row['date_fetched']

    if listing_date not in listing_id_history:
        listing_id_history[listing_date] = set()

    listing_id_history[listing_date].add(listing_id)


class QueryTuner:

    def __init__(self):
        training_data_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('xgboost_model/training_data/listings.json')
            .path
        )
        with open(training_data_json_path, 'r') as training_data_file:
            training_data = json.load(training_data_file)

        df = pd.DataFrame(training_data)
        self.loaded_dates =

    def build_query(self):
        item_categories = external_apis.martial_weapons
        currencies = [
            external_apis.Currency.EXALTED_ORB,
            external_apis.Currency.DIVINE_ORB
        ]

        currency_amounts = [(1, 1)]
        for i in range(1, 8):
            first_num = currency_amounts[i - 1][1] + 1
            second_num = first_num + i * 2
            currency_amounts.append((first_num, second_num))

        for item_category, currency, currency_amount in itertools.product(item_categories, currencies, currency_amounts):
            logging.info(f"\n\n!!! Querying category '{item_category}, currency '{currency}', amount '{currency_amount}!!!\n\n")
            category_filter = external_apis.MetaFilter(
                filter_type_enum=external_apis.TypeFilters.ITEM_CATEGORY,
                filter_value=item_category
            )

            days_since_listed_filter = external_apis.MetaFilter(
                filter_type_enum=external_apis.TradeFilters.LISTED,
                filter_value=ListedSince.UP_TO_1_WEEK
            )

            price_filter = external_apis.MetaFilter(
                filter_type_enum=external_apis.TradeFilters.PRICE,
                filter_value=currency,
                currency_amount=currency_amount
            )

            rarity_filter = external_apis.MetaFilter(
                filter_type_enum=external_apis.TypeFilters.ITEM_RARITY,
                filter_value=external_apis.Rarity.RARE
            )

            meta_mod_filters = [category_filter, price_filter, rarity_filter, days_since_listed_filter]
            query = external_apis.TradeQueryConstructor().create_trade_query(
                meta_mod_filters=meta_mod_filters
            )

            api_item_responses = external_apis.TradeItemsFetcher().fetch_items(query=query)

