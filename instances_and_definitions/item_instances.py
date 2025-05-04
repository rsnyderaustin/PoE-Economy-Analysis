
from abc import ABC

from .utils import ModClass, ModAffixType


class SubMod:
    def __init__(self, mod_id: str, text: str, values_ranges: list):
        self.mod_id = mod_id
        self.text = text
        self.values_ranges = values_ranges


class ItemMod:

    def __init__(self,
                 mod_class: ModClass,
                 mod_name: str,
                 mod_affix_type: ModAffixType,
                 mod_tier: int,
                 sub_mods: list[SubMod]):
        self.mod_class = mod_class
        self.mod_name = mod_name
        self.mod_affix_type = mod_affix_type
        self.mod_tier = mod_tier
        self.sub_mods = sub_mods


class ItemSkill:

    def __init__(self,
                 name: str,
                 level: int):
        self.name = name
        self.level = level


class ItemSocketer:

    def __init__(self, name: str, text: str):
        """
        Socketers have no rolls and thus do not differ from item to item. Their text is static.
        """
        self.name = name
        self.text = text
