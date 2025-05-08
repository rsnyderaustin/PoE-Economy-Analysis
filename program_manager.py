
import itertools
import logging

import data_ingestion
from file_management import FilesManager
from data_ingestion import trade_api
from data_synthesizing.poecd_data_injecter import PoecdDataInjecter
from shared import trade_item_enums
from xgboost_model import DataIngester

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
        self.trade_api_handler = trade_api.TradeApiHandler()
        self.files_manager = FilesManager()
        self.injector = PoecdDataInjecter()
        self.ai_data_prep = DataIngester()

    def execute(self):
        # item_categories = [*trade_item_enums.socketable_items, *trade_item_enums.martial_weapons]
        item_categories = trade_item_enums.martial_weapons
        currencies = [
            trade_item_enums.Currency.EXALTED_ORB,
            trade_item_enums.Currency.DIVINE_ORB
        ]

        currency_amounts = [(1,1)]
        for i in range(1, 8):
            first_num = currency_amounts[i-1][1] + 1
            second_num = first_num + i * 2
            currency_amounts.append((first_num, second_num))

        queries = []
        for item_category, currency, currency_amount in itertools.product(item_categories, currencies, currency_amounts):
            logging.info(f"\n\n!!! Querying category '{item_category}, currency '{currency}', amount '{currency_amount}!!!\n\n")
            ilvl_filter = trade_api.MetaFilter(
                filter_type_enum=trade_item_enums.TypeFilters.ITEM_LEVEL,
                filter_value=(71, 82)
            )

            category_filter = trade_api.MetaFilter(
                filter_type_enum=trade_item_enums.TypeFilters.ITEM_CATEGORY,
                filter_value=item_category
            )

            days_since_listed_filter = trade_api.MetaFilter(
                filter_type_enum=trade_item_enums.TradeFilters.LISTED,
                filter_value=trade_item_enums.ListedSince.UP_TO_1_DAY
            )

            price_filter = trade_api.MetaFilter(
                filter_type_enum=trade_item_enums.TradeFilters.PRICE,
                filter_value=currency,
                currency_amount=currency_amount
            )

            rarity_filter = trade_api.MetaFilter(
                filter_type_enum=trade_item_enums.TypeFilters.ITEM_RARITY,
                filter_value=trade_item_enums.Rarity.RARE
            )

            meta_mod_filters = [ilvl_filter, category_filter, price_filter, rarity_filter, days_since_listed_filter]
            query = trade_api.Query(meta_filters=meta_mod_filters)
            queries.append(query)

        for api_item_responses in self.trade_api_handler.process_queries(queries):
            if not api_item_responses:
                continue

            listings = []
            maps_need_updated = False
            for api_item_response in api_item_responses:
                _clean_item_data(api_item_response['item'])
                listing = data_ingestion.create_listing(api_item_response)
                listings.append(listing)
                new_map_data = self.files_manager.cache_encodings(listing=listing)
                if new_map_data:
                    maps_need_updated = True

                for mod in listing.mods:
                    self.injector.inject_poecd_data_into_mod(item_mod=mod)
                    self.files_manager.cache_mod(item_mod=mod)

            logging.info(f"Created {len(listings)} listings.")

            if maps_need_updated:
                logging.info("Updating AI map data.")
                self.ai_data_prep.update_data()

            self.ai_data_prep.save_data(listings)

            logging.info(f"Saved {len(listings)} listings into AI model training data.")

            self.files_manager.save_data()

