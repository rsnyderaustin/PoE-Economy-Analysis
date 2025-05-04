
from abc import ABC

from .utils import ModClass, ModAffixType


class ItemMod(ABC):

    mod_classes = [e for e in ModClass]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'mod_classes'):
            raise NotImplementedError(f"{cls.__name__} must define a class variable 'mod_classes'")


class SubMod:
    def __init__(self, mod_id: str, text: str, values_ranges: list):
        self.mod_id = mod_id
        self.text = text
        self.values_ranges = values_ranges


class ItemAffixedMod(ItemMod):

    mod_classes = [ModClass.FRACTURED, ModClass.EXPLICIT]

    def __init__(self,
                 mod_class: ModClass,
                 mod_name: str,
                 mod_affix_type: ModAffixType,
                 mod_tier: int,
                 sub_mods: list[SubMod]):
        """
        As of right now this only applies to Explicit mods and Fractured mods.
        I 'think' only Affixed mods can be hybrid - could be wrong though.
        """
        self.mod_class = mod_class
        self.mod_name = mod_name
        self.mod_affix_type = mod_affix_type
        self.mod_tier = mod_tier
        self.sub_mods = sub_mods


class ItemNonAffixedMod(ItemMod):

    mod_classes = [ModClass.RUNE, ModClass.ENCHANT]

    def __init__(self,
                 mod_class: ModClass,
                 mod_text: str,
                 mod_values: list,
                 mod_id: str = None):
        """
        As of right now this only applies to Enchant mods and Implicit mods.
        """
        self.mod_class = mod_class
        self.mod_text = mod_text
        self.mod_values = mod_values

        self.mod_id = mod_id


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
