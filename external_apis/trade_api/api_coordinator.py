import logging
from itertools import product

from data_synthesizing.atype_clasifier import ATypeClassifier
from utils import classifications
from utils.enums import Currency, TradeFilters, TypeFilters, Rarity, ModClass, EquipmentAttribute
from . import helper_funcs
from .api_data_saver import ApiDataSaver
from .querying import (MetaFilter, TradeQueryConstructor)
from .trade_items_fetcher import TradeItemsFetcher


class TradeApiCoordinator:

    def __init__(self):
        self.api_data_saver = ApiDataSaver()
        self.api_data_fetcher = TradeItemsFetcher()

    def sample_items_generator(self):
        price_ranges = []
        for i in range(0, 100, 11):
            price_ranges.append((i, i + 10))

        currencies = [
            Currency.CHAOS_ORB,
            Currency.EXALTED_ORB,
            Currency.DIVINE_ORB
        ]

        query_combos = list(
            product(
                list(classifications.socketable_items),
                currencies,
                price_ranges
            )
        )

        for item_category, currency, price_range in query_combos:
            logging.info(f"Querying:"
                         f"\n\tItem Category: {item_category}"
                         f"\n\tCurrency: {currency}"
                         f"\n\tPrice range: {price_range}")

            rarity_filter = MetaFilter(
                meta_filter_enum=TypeFilters.ITEM_RARITY,
                mod_value=Rarity.RARE.value
            )
            price_filter = MetaFilter(
                meta_filter_enum=TradeFilters.PRICE,
                mod_value=(price_range[0], price_range[1]),
                price_currency_enum=currency
            )
            rune_socket_filter = MetaFilter(
                meta_filter_enum=EquipmentAttribute.RUNE_SOCKETS,
                mod_value=(1, 1)
            )
            only_armour_filter = MetaFilter(
                meta_filter_enum=TypeFilters.ITEM_CATEGORY,
                mod_value=item_category.value
            )
            query = TradeQueryConstructor().create_trade_query(
                meta_mod_filters=[rarity_filter, price_filter, only_armour_filter, rune_socket_filter]
            )

            api_items = self.api_data_fetcher.fetch_items(query=query)

            for item in api_items:
                return item

            for item_response in api_items:
                if ModClass.RUNE.value in item_response['item']:
                    runes = RunesCreator.create_runes(item_response['item'])
                else:
                    continue

                if not runes:
                    continue

                item_atype = ATypeClassifier.convert(item_data=item_response['item'])
                item_atype = helper_funcs.remove_piped_brackets(item_atype)

                self.api_data_saver.save_runes(
                    item_atype=item_atype,
                    runes=runes
                )

                self.api_data_saver.export_data()

            for item_response in api_items:
                listing = ListingCreator.create_listing(api_item_response=item_response)

                self.api_data_saver.save_listing(listing=listing)
