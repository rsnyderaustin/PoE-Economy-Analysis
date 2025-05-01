import logging
from itertools import product

from utils import classifications
from utils.enums import Currency, TradeFilters, TypeFilters, Rarity, ModClass, EquipmentAttribute
from .api_data_saver import ApiDataSaver
from .atype_clasifier import ATypeClassifier
from .creators.runes_creator import RunesCreator
from .querying import (MetaModFilter, TradeQueryConstructor)
from .trade_items_fetcher import TradeItemsFetcher


class TradeApiCoordinator:

    def __init__(self):
        self.api_data_saver = ApiDataSaver()
        self.api_data_fetcher = TradeItemsFetcher()

    def fill_internal_data(self):
        price_ranges = []
        for i in range(0, 300, 3):
            price_ranges.append((i, i + 2))

        currencies = [
            Currency.CHAOS_ORB,
            Currency.EXALTED_ORB,
            Currency.DIVINE_ORB
        ]

        result = list(product(
            list(classifications.socketable_item_categories),
            currencies,
            price_ranges
        ))

        for item_category, currency, price_range in result:
            logging.info(f"Querying:"
                         f"\n\tItem Category: {item_category}"
                         f"\n\tCurrency: {currency}"
                         f"\n\tPrice range: {price_range}")

            rarity_filter = MetaModFilter(
                meta_filter_enum=TypeFilters.ITEM_RARITY,
                mod_value=Rarity.MAGIC.value
            )
            price_filter = MetaModFilter(
                meta_filter_enum=TradeFilters.PRICE,
                mod_value=(price_range[0], price_range[1]),
                price_currency_enum=Currency.EXALTED_ORB
            )
            rune_socket_filter = MetaModFilter(
                meta_filter_enum=EquipmentAttribute.RUNE_SOCKETS,
                mod_value=(1, 1)
            )
            only_armour_filter = MetaModFilter(
                meta_filter_enum=TypeFilters.ITEM_CATEGORY,
                mod_value=item_category.value
            )
            query = TradeQueryConstructor().create_trade_query(
                meta_mod_filters=[rarity_filter, price_filter, only_armour_filter, rune_socket_filter]
            )

            api_items = self.api_data_fetcher.fetch_items(query=query)

            for item_response in api_items:
                if ModClass.RUNE.value in item_response['item']:
                    runes = RunesCreator.create_runes(item_response['item'])
                else:
                    continue

                if not runes:
                    continue

                self.api_data_saver.save_runes(
                    item_atype=ATypeClassifier.convert(item_data=item_response['item']),
                    runes=runes
                )

                self.api_data_saver.export_data()
