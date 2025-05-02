
import re

from utils.enums import ModifierClass, ModAffixType, ItemCategory
from data_synthesizing.mods import ModTier
from things.items.mod import Mod
from .socketer import Socketer


class Modifiable:

    def __init__(self,
                 item_id: str,
                 name: str,
                 category: ItemCategory,
                 btype: str,
                 atype: str,
                 quality: int,
                 corrupted: bool,
                 ilvl: int,
                 rarity: str = None,
                 num_sockets: int = None,
                 socketed_items: list[Socketer] = None,
                 implicit_mods: list[ModTier] = None,
                 explicit_mods: list[ModTier] = None,
                 enchant_mods: list[ModTier] = None,
                 rune_mods: list[ModTier] = None,
                 fractured_mods: list[ModTier] = None
                 ):
        self.item_id = item_id
        self.name = name
        self.btype = btype
        self.corrupted = corrupted
        self.quality = quality
        self.category = category
        self.ilvl = ilvl
        self.atype = atype

        self.rarity = rarity
        self.num_sockets = num_sockets
        self.socketed_items = socketed_items

        self.implicit_mods = implicit_mods or []
        self.explicit_mods = explicit_mods or []
        self.enchant_mods = enchant_mods or []
        self.rune_mods = rune_mods or []
        self.fractured_mods = fractured_mods or []

    @property
    def maximum_quality(self):
        for mod in self.implicit_mods:
            if bool(re.fullmatch(r"Maximum Quality is \d+%", mod.mod_text)):
                return re.search(r'\d+', mod.mod_text).group()


    @property
    def mods(self):
        return self.explicit_mods + self.fractured_mods

    @property
    def prefixes(self):
        return [mod for mod in self.mods
                if mod.affix_type == ModAffixType.PREFIX]

    @property
    def suffixes(self):
        return [mod for mod in self.mods
                if mod.affix_type == ModAffixType.SUFFIX.value]

    @property
    def permanent_mods(self) -> list:
        return self.fractured_mods

    @property
    def removable_mods(self) -> list:
        return self.removable_prefixes + self.removable_suffixes

    @property
    def removable_prefixes(self) -> list:
        changeable_prefixes = [mod for mod in self.explicit_mods
                               if mod.affix_type == ModAffixType.PREFIX]
        return changeable_prefixes

    @property
    def removable_suffixes(self) -> list:
        changeable_suffixes = [mod for mod in self.explicit_mods
                               if mod.affix_type == ModAffixType.SUFFIX]
        return changeable_suffixes





