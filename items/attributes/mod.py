
from dataclasses import dataclass
from enum import Enum

from utils import ItemAttributes


@dataclass
class Mod:
    mod_enum: Enum
    mod_class: ItemAttributes.Modifier
    numeric_values: list
    mod_string: str

