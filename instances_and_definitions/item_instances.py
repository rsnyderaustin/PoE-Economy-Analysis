import datetime
import re
from typing import Iterable

from shared.enums.item_enums import ModAffixType, AType
from shared.enums.trade_enums import ModClass, Rarity, Currency


class SubMod:
    def __init__(self,
                 mod_id: str,
                 sanitized_mod_text: str,
                 actual_values: list = None,
                 values_ranges: list[tuple[float, float]] | list[tuple[int, int]] = None):
        self.mod_id = mod_id
        self.actual_values = actual_values
        self.sanitized_mod_text = sanitized_mod_text
        self.values_ranges = values_ranges


def generate_mod_id(atype: str,
                    mod_ids: Iterable,
                    affix_type: ModAffixType = None):
    atype = atype.lower().replace(' ', '_')
    mod_ids = sorted(list(mod_ids))

    return atype, *mod_ids, affix_type


class ItemMod:

    def __init__(self,
                 atype: str,
                 mod_class_e: ModClass,
                 mod_name: str,
                 affix_type_e: ModAffixType,
                 mod_tier: int,
                 mod_ilvl: int,
                 sub_mods: list[SubMod] = None):
        self.atype = atype
        self.mod_class_e = mod_class_e
        self.mod_name = mod_name
        self.affix_type_e = affix_type_e
        self.mod_tier = mod_tier
        self.mod_ilvl = mod_ilvl
        self.sub_mods = sorted(sub_mods, key=lambda sm: sm.mod_id) if sub_mods else []

        # These variables should be very quickly filled in after creation
        self.mod_types = None
        self.weighting = None

    def __eq__(self, other):
        if not isinstance(other, ItemMod):
            return False

        return self.mod_id == other.mod_id

    @property
    def is_hybrid(self):
        return len(self.sub_mods) >= 2

    @property
    def mod_id(self):
        return generate_mod_id(atype=self.atype,
                               mod_ids=[sub_mod.mod_id for sub_mod in self.sub_mods],
                               affix_type=self.affix_type_e)

    @property
    def mod_values(self):
        return [sub_mod.actual_values for sub_mod in self.sub_mods]

    def insert_sub_mods(self, sub_mods: list[SubMod]):
        self.sub_mods = sorted(sub_mods, key=lambda sm: sm.mod_id)

    def get_sub_mods(self):
        return self.sub_mods


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
                 date_fetched: datetime,
                 minutes_since_listed: float,
                 minutes_since_league_start: float,
                 currency: Currency,
                 currency_amount: int,
                 item_name: str,
                 item_btype: str,  # Hunting Shoes, Lunar Amulet, etc
                 item_atype: str,  # DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
                 item_category: AType,
                 rarity: Rarity,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 implicit_mods: list[ItemMod],
                 enchant_mods: list[ItemMod],
                 fractured_mods: list[ItemMod],
                 explicit_mods: list[ItemMod],
                 item_skills: list[ItemSkill],
                 item_properties: dict
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
        self.implicit_mods = implicit_mods
        self.enchant_mods = enchant_mods
        self.item_skills = item_skills
        self.fractured_mods = fractured_mods
        self.explicit_mods = explicit_mods
        self.item_properties = item_properties

        self._mod_class_to_attribute = {
            ModClass.IMPLICIT: self.implicit_mods,
            ModClass.ENCHANT: self.enchant_mods,
            ModClass.FRACTURED: self.fractured_mods,
            ModClass.EXPLICIT: self.explicit_mods
        }

    def __hash__(self):
        return hash((self.listing_id, self.minutes_since_listed))

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
    def removable_mods(self) -> list[ItemMod]:
        return self.explicit_mods

    @property
    def quality(self):
        return getattr(self.item_properties, 'quality', 0)

    @quality.setter
    def quality(self, new_quality):
        self.item_properties['quality'] = new_quality

    @property
    def max_quality(self):
        return self._determine_max_quality()

    def set_quality(self, new_quality: int):
        self.item_properties['quality'] = new_quality

    @property
    def prefixes(self):
        return [mod for mod in self.mods if mod.affix_type_e == ModAffixType.PREFIX]

    @property
    def open_prefixes(self) -> int:
        if self.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type_e == ModAffixType.PREFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type_e == ModAffixType.PREFIX])

    @property
    def suffixes(self):
        return [mod for mod in self.mods if mod.affix_type_e == ModAffixType.SUFFIX]

    @property
    def open_suffixes(self) -> int:
        if self.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type_e == ModAffixType.SUFFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type_e == ModAffixType.SUFFIX])

    def fetch_mods(self, mod_class: ModClass):
        return self._mod_class_to_attribute[mod_class]
