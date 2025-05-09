import itertools
import logging
from dataclasses import dataclass
from enum import Enum

from data_ingestion import trade_api
from shared import trade_item_enums


class MetaFilter:

    def __init__(self,
                 filter_type_enum: Enum,
                 filter_value: Enum | tuple | bool,
                 currency_amount: tuple = None):
        """

        :param filter_type_enum:
        :param filter_value:If a tuple, the first element is min and second is max
        :param currency_amount: First tuple element is min and second tuple element is max
        """
        self.meta_search_type = trade_item_enums.filter_enum_to_meta_search_type[filter_type_enum]
        self.filter_type = filter_type_enum.value
        self.filter_value = filter_value.value if isinstance(filter_value, Enum) else filter_value

        self.currency_amount = currency_amount


class StatFilter:

    def __init__(self,
                 mod_enum: Enum,
                 values_range: tuple = None,
                 weight: float = None):
        self.mod_enum = mod_enum
        self.values_range = values_range
        self.weight = weight


@dataclass
class StatsFiltersGroup:
    filter_type: trade_item_enums.StatSearchType
    mod_filters: list[StatFilter]
    value_range: tuple = None


class Query:

    def __init__(self,
                 meta_filters: list[MetaFilter] = None,
                 stats_filters_groups: list[StatsFiltersGroup] = None):
        self.meta_filters = meta_filters or []
        self.stats_filters_groups = stats_filters_groups or []


class QueryPresets:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(QueryPresets, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.training_fills = self._training_fill()

    def _training_fill(self):
        # item_categories = [*trade_item_enums.socketable_items, *trade_item_enums.martial_weapons]
        item_categories = trade_item_enums.martial_weapons
        currencies = [
            trade_item_enums.Currency.EXALTED_ORB,
            trade_item_enums.Currency.DIVINE_ORB
        ]

        currency_amounts = [(1, 1)]
        for i in range(1, 8):
            first_num = currency_amounts[i - 1][1] + 1
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

        return queries
