
import logging

import data_ingestion
import external_apis
from data_exporting import ExportManager
from shared import ATypeClassifier

logging.basicConfig(level=logging.INFO,
                    force=True)


class ProgramManager:

    def __init__(self):
        self.export_manager = ExportManager()

    def execute(self):
        atype_classifier = ATypeClassifier()

        one_hand_mace_filter = external_apis.MetaFilter(
            filter_type_enum=external_apis.TypeFilters.ITEM_CATEGORY,
            filter_value=external_apis.ItemCategory.ONE_HANDED_MACE
        )

        price_filter = external_apis.MetaFilter(
            filter_type_enum=external_apis.TradeFilters.PRICE,
            filter_value=external_apis.Currency.DIVINE_ORB,
            currency_amount=(1, 5)
        )

        rarity_filter = external_apis.MetaFilter(
            filter_type_enum=external_apis.TypeFilters.ITEM_RARITY,
            filter_value=external_apis.Rarity.RARE
        )

        meta_mod_filters = [one_hand_mace_filter, price_filter, rarity_filter]
        query = external_apis.TradeQueryConstructor().create_trade_query(
            meta_mod_filters=meta_mod_filters
        )

        api_item_responses = external_apis.TradeItemsFetcher().fetch_items(query=query)

        mods = [
            data_ingestion.create_item_mods(item_data=api_item_response['item'])
            for api_item_response in api_item_responses
        ]

        runes = [
            data_ingestion.create_socketer_for_internal_storage(item_data=api_item_response['item'])
            for api_item_response in api_item_responses
        ]

        x=0

