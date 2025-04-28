
from dataclasses import dataclass
from enum import Enum
from typing import Any


class MetaSearchType(Enum):
    EQUIPMENT = 'equipment_filters'
    TRADE = 'trade_filters'
    REQUIREMENT = 'req_filters'
    TYPE = 'type_filters'
    MISC = 'misc_filters'


@dataclass
class MetaModFilter:
    meta_mod_name_enum: Enum
    mod_value: Any


class MetaFiltersGroup:

    def __init__(self,
                 search_type: MetaSearchType,
                 meta_mod_filters: list[MetaModFilter]):
        self.search_type = search_type
        self.meta_mod_filters = meta_mod_filters

