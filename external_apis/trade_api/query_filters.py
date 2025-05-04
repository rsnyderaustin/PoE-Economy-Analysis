from dataclasses import dataclass
from enum import Enum

from . import trade_api_utils


class MetaFilter:

    def __init__(self,
                 filter_type_enum: Enum,
                 filter_value: Enum | bool,
                 currency_amount: tuple = None):
        """

        :param filter_type_enum:
        :param filter_value:
        :param currency_amount: First tuple element is min and second tuple element is max
        """
        self.meta_search_type = trade_api_utils.filter_enum_to_meta_search_type[filter_type_enum]
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
    filter_type: trade_api_utils.StatSearchType
    mod_filters: list[StatFilter]
    value_range: tuple = None


