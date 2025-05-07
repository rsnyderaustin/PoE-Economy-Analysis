
import logging
import itertools

import data_ingestion
import external_apis
from data_exporting import ExportManager
from data_synthesizing.poecd_data_injecter import PoecdDataInjecter
from external_apis import ItemCategory, ListedSince
from shared import ATypeClassifier
from xgboost_model import DataPrep

logging.basicConfig(level=logging.INFO,
                    force=True)


def _clean_item_data(item_data: dict):
    """
    Right now this is just used to clear empty implicits from spears granting skill Spear Throw.
    """
    if 'extended' in item_data and item_data['extended'] and 'implicit' in item_data['extended']['mods']:
        implicit_mod_dicts = item_data['extended']['mods']['implicit']

        implicit_mod_dicts[:] = [
            implicit_mod_dict
            for implicit_mod_dict in implicit_mod_dicts
            if (implicit_mod_dict['magnitudes'] or implicit_mod_dict['name'] or implicit_mod_dict['tier'])
        ]


class ProgramManager:

    def __init__(self):
        self.export_manager = ExportManager()
        self.injector = PoecdDataInjecter()
        self.ai_data_prep = DataPrep()

    def execute(self):
        # item_categories = [*external_apis.socketable_items, *external_apis.martial_weapons]
        item_categories = external_apis.martial_weapons
        currencies = [
            external_apis.Currency.EXALTED_ORB,
            external_apis.Currency.DIVINE_ORB
        ]

        currency_amounts = [(1,1)]
        for i in range(1, 8):
            first_num = currency_amounts[i-1][1] + 1
            second_num = first_num + i * 2
            currency_amounts.append((first_num, second_num))

        for item_category, currency, currency_amount in itertools.product(item_categories, currencies, currency_amounts):
            logging.info(f"\n\n!!! Querying category '{item_category}, currency '{currency}', amount '{currency_amount}!!!\n\n")
            ilvl_filter = external_apis.MetaFilter(
                filter_type_enum=external_apis.TypeFilters.ITEM_LEVEL,
                filter_value=(75,)
            )

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

            listings = []
            maps_need_updated = False
            for api_item_response in api_item_responses:
                _clean_item_data(api_item_response['item'])
                listing = data_ingestion.create_listing(api_item_response)
                listings.append(listing)
                new_map_data = self.export_manager.aggregate_save_to_maps(listing=listing)
                if new_map_data:
                    maps_need_updated = True

                for mod in listing.mods:
                    self.injector.inject_poecd_data_into_mod(item_mod=mod)
                    self.export_manager.save_mod(item_mod=mod)

            logging.info(f"Created {len(listings)} listings.")

            if maps_need_updated:
                logging.info("Updating AI map data.")
                self.ai_data_prep.update_data()

            for listing in listings:
                self.ai_data_prep.save_data(listing)
            logging.info(f"Saved {len(listings)} lists into AI model training data.")

            self.export_manager.export_data()

