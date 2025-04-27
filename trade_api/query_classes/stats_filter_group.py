
from dataclasses import dataclass
from enum import Enum

from utils import modifier_enum_classes, StatFilterType


class StatModFilter:

    def __init__(self,
                 mod_enum: Enum,
                 values_range: tuple = None,
                 weight: float = None):
        if mod_enum.__class__ not in modifier_enum_classes:
            raise TypeError(f"Mod of class {mod_enum.__class__} is not one of "
                            f"acceptable classes {modifier_enum_classes}")

        self.mod_enum = mod_enum
        self.values_range = values_range
        self.weight = weight


@dataclass
class StatsFiltersGroup:
    filter_type: StatFilterType
    mod_filters: list[StatModFilter]
    value_range: tuple = None

