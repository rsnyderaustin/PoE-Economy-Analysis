from dataclasses import dataclass
from enum import Enum

from . import trade_api_utils


class MetaFilter:

    def __init__(self,
                 meta_enum: Enum,
                 currency: trade_api_utils.Currency = None,
                 currency_amount: tuple = None):
        """

        :param meta_enum:
        :param currency:
        :param currency_amount: First tuple element is min and second tuple element is max
        """
        self.meta_enum = trade_api_utils.filter_enum_to_meta_search_type(meta_enum)

        self.currency = currency
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


