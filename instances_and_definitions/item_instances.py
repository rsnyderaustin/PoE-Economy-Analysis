import re

from shared.trade_item_enums import ItemCategory
from .utils import ModClass, ModAffixType, generate_mod_id


class SubMod:
    def __init__(self,
                 mod_id: str,
                 actual_values: tuple[float],
                 sanitized_mod_text: str,
                 values_ranges: list[tuple[float | None, float | None]]):
        self.mod_id = mod_id
        self.actual_values = actual_values
        self.sanitized_mod_text = sanitized_mod_text
        self.values_ranges = values_ranges


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

        # These variables should be very quickly filled in after creation
        self.mod_types = None
        self.weighting = None

    @property
    def is_hybrid(self):
        return len(self.sub_mods) >= 2

    @property
    def mod_id(self):
        return generate_mod_id(atype=self.atype,
                               mod_ids=[sub_mod.mod_id for sub_mod in self.sub_mods],
                               affix_type=self.affix_type)


class ItemSkill:

    def __init__(self,
                 name: str,
                 level: int = None):
        self.name = name
        self.level = level or 1


class ItemSocketer:

    def __init__(self, sanitized_socketer_text: str, actual_values: tuple | None):
        """
        Socketers have no rolls and thus do not differ from item to item. Their text is static.
        """
        self.sanitized_socketer_text = sanitized_socketer_text
        self.actual_values = actual_values


class ModifiableListing:

    def __init__(self,
                 account_name: str,
                 listing_id: str,
                 date_fetched: str,
                 minutes_since_listed: float,
                 minutes_since_league_start: float,
                 currency: str,
                 currency_amount: int,
                 item_name: str,
                 item_btype: str,  # Hunting Shoes, Lunar Amulet, etc
                 item_atype: str,  # DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
                 item_category: ItemCategory,
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
                 fractured_mods: list[ItemMod],
                 explicit_mods: list[ItemMod],
                 socketers: list[ItemSocketer],
                 open_sockets: int,
                 item_skills: list[ItemSkill],
                 item_properties: dict = None
                 ):
        self.account_name = account_name
        self.listing_id = listing_id
        self.date_fetched = date_fetched
        self.minutes_since_listed = minutes_since_listed
        self.minutes_since_league_start = minutes_since_league_start
        self.currency = currency
        self.currency_amount = currency_amount
        self.item_name = item_name
        self.item_btype = item_btype
        self.item_category = item_category
        self.item_atype = item_atype
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
        self.open_sockets = open_sockets
        self.socketers = socketers
        self.item_skills = item_skills
        self.fractured_mods = fractured_mods
        self.explicit_mods = explicit_mods

        self.item_properties = item_properties or {}

        self.maximum_quality = self._determine_max_quality()

    def _determine_max_quality(self) -> int:
        implicit_sub_mods = [sub_mod for mod in self.implicit_mods for sub_mod in mod.sub_mods]
        max_quality = 20
        for sub_mod in implicit_sub_mods:
            if bool(re.fullmatch(r"maximum_quality_is", sub_mod.sanitized_mod_text)):
                max_quality = sub_mod.actual_values[0]

        return max_quality

    @property
    def mods(self) -> list[ItemMod]:
        all_mods = (
                self.implicit_mods +
                self.enchant_mods +
                self.fractured_mods +
                self.explicit_mods
        )
        return all_mods

    @property
    def affixed_mods(self) -> list[ItemMod]:
        return self.explicit_mods + self.fractured_mods

    @property
    def quality(self):
        return self.item_properties['Quality']

    def set_quality(self, new_quality: int):
        self.item_properties['Quality'] = new_quality

    @property
    def permanent_mods(self) -> list[ItemMod]:
        return self.fractured_mods

    @property
    def removable_mods(self) -> list[ItemMod]:
        return self.explicit_mods

    @property
    def prefixes(self):
        return [mod for mod in self.mods if mod.affix_type == ModAffixType.PREFIX]

    @property
    def open_prefixes(self) -> int:
        return 3 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.PREFIX])

    @property
    def suffixes(self):
        return [mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX]

    @property
    def open_suffixes(self) -> int:
        return 3 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX])
