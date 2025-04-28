
from dataclasses import dataclass
from enum import Enum

from utils.enums import ModAffixType


@dataclass
class Mod:
    official_poe_mod_id: str
    readable_name: str
    numeric_values: list
    affix_type: ModAffixType

