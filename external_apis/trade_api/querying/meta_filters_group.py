
from dataclasses import dataclass
from enum import Enum
from typing import Any

from utils.enums import MetaSearchType


@dataclass
class MetaModFilter:
    meta_attribute_enum: Enum
    mod_value: Any


class MetaFiltersGroup:

    def __init__(self,
                 search_type: MetaSearchType,
                 meta_mod_filters: list[MetaModFilter]):
        self.search_type = search_type
        self.meta_mod_filters = meta_mod_filters

