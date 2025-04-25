
from dataclasses import dataclass
from utils import ItemAttributes


@dataclass
class Mod:
    mod_class: ItemAttributes.Modifier
    numeric_values: list
    mod_string: str

