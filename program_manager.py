
import logging
import itertools

import data_ingestion
import external_apis
from data_exporting import ExportManager
from data_synthesizing.poecd_data_injecter import PoecdDataInjecter

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

    def execute(self):
        item_categories = [*external_apis.socketable_items, *external_apis.martial_weapons]
        currencies = [
            external_apis.Currency.EXALTED_ORB,
            external_apis.Currency.CHAOS_ORB,
            external_apis.Currency.DIVINE_ORB
        ]
        currency_amounts = [(i, i + 2) for i in range(0, 50, 3)]
        for item_category, currency, currency_amount in itertools.product(item_categories, currencies, currency_amounts):
            logging.info(f"\n\n!!! Querying category '{item_category}, currency '{currency}', amount '{currency_amount}!!!\n\n")
            category_filter = external_apis.MetaFilter(
                filter_type_enum=external_apis.TypeFilters.ITEM_CATEGORY,
                filter_value=item_category
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

            meta_mod_filters = [category_filter, price_filter, rarity_filter]
            query = external_apis.TradeQueryConstructor().create_trade_query(
                meta_mod_filters=meta_mod_filters
            )

            api_item_responses = external_apis.TradeItemsFetcher().fetch_items(query=query)

            for api_item_response in api_item_responses:
                _clean_item_data(api_item_response['item'])
                mods = data_ingestion.create_item_mods(item_data=api_item_response['item'])
                for mod in mods:
                    self.injector.inject_poecd_data_into_mod(item_mod=mod)
                    self.export_manager.save_mod(item_mod=mod)

                """socketer = data_ingestion.create_socketer_for_internal_storage(item_data=api_item_response['item'])
                self.export_manager.save_rune(atype=ATypeClassifier.classify(item_data=api_item_response['item']),
                                              rune_name=socketer.name,
                                              rune_effect=socketer.text)"""

            self.export_manager.export_data()

