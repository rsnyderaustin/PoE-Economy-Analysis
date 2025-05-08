from dataclasses import dataclass
from enum import Enum

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
