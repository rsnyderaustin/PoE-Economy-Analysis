import re

from external_apis import ItemCategory
from .utils import ModClass, ModAffixType, generate_mod_id


class SubMod:
    def __init__(self,
                 mod_id: str,
                 mod_text: str,
                 values_ranges: list[tuple[float | None, float | None]]):
        self.mod_id = mod_id
        self.mod_text = mod_text

        min_roll_total = 0.0
        max_roll_total = 0.0
        for min_val, max_val in values_ranges:
            min_roll_total += min_val or 0
            max_roll_total += max_val or 0

        self.values_range = (min_roll_total, max_roll_total)


class ItemMod:

    def __init__(self,
                 atype: str,
                 mod_class: ModClass,
                 mod_name: str,
                 affix_type: ModAffixType,
                 mod_tier: int,
                 mod_ilvl: int,
                 sub_mods: list[SubMod]):
        self.atype = atype
        self.mod_class = mod_class
        self.mod_name = mod_name
        self.affix_type = affix_type
        self.mod_tier = mod_tier
        self.mod_ilvl = mod_ilvl
        self.sub_mods = sub_mods

        # This is filled in later via Poecd data
        self.mod_types = None
        self.weighting = None

    @property
    def is_hybrid(self):
        return len(self.sub_mods) >= 2

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


class ModifiableListing:

    def __init__(self,
                 listing_id: str,
                 date_fetched: str,
                 price_currency: str,
                 price_amount: int,
                 item_name: str,
                 item_btype: str,  # Hunting Shoes, Lunar Amulet, etc
                 item_atype: str,  # DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
                 item_bgroup: str,  # Armour, Weapon, etc
                 rarity: str,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 level_requirement: int,
                 str_requirement: int,
                 int_requirement: int,
                 dex_requirement: int,
                 implicit_mods: list[ItemMod],
                 enchant_mods: list[ItemMod],
                 rune_mods: list[ItemMod],
                 item_skills: list[ItemSkill],
                 fractured_mods: list[ItemMod],
                 explicit_mods: list[ItemMod]
                 ):
        self.listing_id = listing_id
        self.date_fetched = date_fetched
        self.price_currency = price_currency
        self.price_amount = price_amount
        self.item_name = item_name
        self.item_btype = item_btype
        self.item_atype = item_atype
        self.item_bgroup = item_bgroup
        self.rarity = rarity
        self.ilvl = ilvl
        self.identified = identified
        self.corrupted = corrupted
        self.level_requirement = level_requirement
        self.str_requirement = str_requirement
        self.int_requirement = int_requirement
        self.dex_requirement = dex_requirement
        self.implicit_mods = implicit_mods
        self.enchant_mods = enchant_mods
        self.rune_mods = rune_mods
        self.item_skills = item_skills
        self.fractured_mods = fractured_mods
        self.explicit_mods = explicit_mods

    @property
    def mods(self) -> list[ItemMod]:
        all_mods = (
                self.implicit_mods +
                self.enchant_mods +
                self.rune_mods +
                self.fractured_mods +
                self.explicit_mods
        )
        return all_mods


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
                 socketed_items: list[ItemSocketer] = None,
                 implicit_mods: list[ItemMod] = None,
                 explicit_mods: list[ItemMod] = None,
                 enchant_mods: list[ItemMod] = None,
                 rune_mods: list[ItemMod] = None,
                 fractured_mods: list[ItemMod] = None
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
