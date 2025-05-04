
from abc import ABC

from .utils import ModClass, ModAffixType, generate_mod_id


class SubMod:
    def __init__(self, mod_id: str, mod_text: str, values_ranges: list):
        self.mod_id = mod_id
        self.mod_text = mod_text
        self.values_ranges = values_ranges


class ItemMod:

    def __init__(self,
                 atype: str,
                 mod_class: ModClass,
                 mod_name: str,
                 affix_type: ModAffixType,
                 mod_tier: int,
                 sub_mods: list[SubMod]):
        self.atype = atype
        self.mod_class = mod_class
        self.mod_name = mod_name
        self.affix_type = affix_type
        self.mod_tier = mod_tier
        self.sub_mods = sub_mods

    @property
    def mod_id(self):
        return generate_mod_id(atype=self.atype,
                               mod_ids=[sub_mod.mod_id for sub_mod in self.sub_mods],
                               mod_texts=[sub_mod.mod_text for sub_mod in self.sub_mods]
                               )


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
