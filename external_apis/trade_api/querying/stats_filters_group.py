
from dataclasses import dataclass
from enum import Enum

from utils.enums import StatFilterType


class StatModFilter:

    def __init__(self,
                 mod_enum: Enum,
                 values_range: tuple = None,
                 weight: float = None):
        self.mod_enum = mod_enum
        self.values_range = values_range
        self.weight = weight


@dataclass
class StatsFiltersGroup:
    filter_type: StatFilterType
    mod_filters: list[StatModFilter]
    value_range: tuple = None
