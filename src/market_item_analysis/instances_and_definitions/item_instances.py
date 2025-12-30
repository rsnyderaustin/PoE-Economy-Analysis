import datetime
import re
import uuid
from dataclasses import dataclass
from typing import Iterable

from src.market_item_analysis.shared.enums.item_enums import ModAffixType, EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Rarity, Currency


class SubMod:
    def __init__(self,
                 sub_mod_hash: str,
                 sanitized_text: str,
                 actual_values: list = None,
                 values_ranges: list[tuple[float, float]] | list[tuple[int, int]] = None):
        self.sub_mod_hash = sub_mod_hash
        self.sanitized_text = sanitized_text

        # When the ItemMod is stored as a template, its sub-mod values are empty
        self.actual_values = actual_values
        self.values_ranges = values_ranges


def generate_mod_id(mod_class: ModClass,
                    atype: EquipmentCategory,
                    sub_mod_hashes: Iterable,
                    mod_tier: int = None,
                    affix_type: ModAffixType = None):
    atype = atype.value.lower().replace(' ', '_')
    sub_mod_hashes = sorted(list(sub_mod_hashes))

    return mod_class, atype, *sub_mod_hashes, mod_tier, affix_type


class ItemMod:

    def __init__(self,
                 atype: EquipmentCategory,
                 mod_class: ModClass,
                 mod_name: str,
                 affix_type: ModAffixType,
                 mod_tier: int,
                 mod_ilvl: int,
                 sub_mods: list[SubMod] = None):
        self.atype = atype
        self.mod_class = mod_class
        self.mod_name = mod_name
        self.affix_type = affix_type
        self.mod_tier = mod_tier
        self.mod_ilvl = mod_ilvl
        self.sub_mods = sorted(sub_mods, key=lambda sm: sm.sub_mod_hash) if sub_mods else []

        # These variables should be very quickly filled in after creation if applicable
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
                               sub_mod_hashes=[sub_mod.sub_mod_hash for sub_mod in self.sub_mods],
                               affix_type=self.affix_type,
                               mod_class=self.mod_class)

    @property
    def mod_values(self):
        return [sub_mod.actual_values for sub_mod in self.sub_mods]

    @property
    def sub_mod_ids(self):
        return [sub_mod.sub_mod_hash for sub_mod in self.sub_mods]

    def insert_sub_mods(self, sub_mods: list[SubMod]):
        self.sub_mods = sorted(sub_mods, key=lambda sm: sm.sub_mod_hash)

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


class ListingMetadata:

    def __init__(self,
                 poster_account_name: str,
                 listing_id: str,
                 date_posted: datetime,
                 date_fetched: datetime):
        self.poster_account_name = poster_account_name
        self.listing_id = listing_id
        self.date_posted = date_posted
        self.date_fetched = date_fetched

class ItemRequirements:

    def __init__(self,
                 player_level: int,
                 strength: int,
                 intelligence: int,
                 dexterity: int):
        self.player_level = player_level
        self.strength = strength
        self.intelligence = intelligence
        self.dexterity = dexterity


class ItemMods:

    def __init__(self,
                 implicits: list[ItemMod] | None = None,
                 enchants: list[ItemMod] | None = None,
                 fractures: list[ItemMod] | None = None,
                 explicits: list[ItemMod] | None = None):
        self.implicits = implicits or []
        self.enchants = enchants or []
        self.fractures = fractures or []
        self.explicits = explicits or []

        self._mod_class_d = {
            ModClass.IMPLICIT: self.implicits,
            ModClass.ENCHANT: self.enchants,
            ModClass.FRACTURED: self.fractures,
            ModClass.EXPLICIT: self.explicits
        }

    @property
    def all_mods(self) -> list[ItemMod]:
        return [m
                for mods_list in self._mod_class_d.values()
                for m in mods_list]

    def fetch_mods(self, mod_class: ModClass) -> list[ItemMod]:
        return self._mod_class_d[mod_class]


class ItemTypes:

    def __init__(self,
                 base_name: str,
                 item_category: EquipmentCategory):
        """

        :param base_name: Ex: Hunting Shoes, Lunar Amulet, etc
        :param item_category: Ex: DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
        """
        self.base_name = base_name
        self.item_category = item_category


class Price:

    def __init__(self,
                 currency: Currency,
                 amount: int):
        self.currency = currency
        self.amount = amount


class ItemProperties:

    def __init__(self,
                 rarity: Rarity,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 quality: int,
                 **additional_properties):
        self.rarity = rarity
        self.ilvl = ilvl
        self.identified = identified
        self.corrupted = corrupted
        self.quality = quality

        self.additional_properties = additional_properties

class EquipmentListing:

    def __init__(self,
                 metadata: ListingMetadata,
                 price: Price,
                 item_name: str,
                 types: ItemTypes,
                 requirements: ItemRequirements,
                 mods: ItemMods,
                 skills: list[ItemSkill],
                 properties: ItemProperties,
                 internal_id: int = None
                 ):
        self.metadata = metadata
        self.price = price
        self.item_name = item_name
        self.types = types
        self.requirements = requirements
        self.mods_ = mods
        self.skills = skills
        self.properties = properties

        self.internal_id = internal_id or uuid.uuid4().hex

        # This is lazy loaded when loading into the PricePrediction model
        self.divs = None

    def __hash__(self):
        return hash((self.listing_id, self.minutes_since_listed))

    def __str__(self):
        if rp._item_properties:
            properties_ = {
                shared_utils.extract_from_brackets(p['name']): shared_utils.extract_values_from_text(p['values'][0][0])[0]
                for p in rp._item_properties[1:]
            }
        else:
            properties_ = {}

        att_requirements = {
            k: v for k, v in {
                'Str': rp.str_requirement,
                'Dex': rp.dex_requirement,
                'Int': rp.int_requirement
            }.items() if v
        }

        implicits = rp.fetch_tiered_mod_strings(mod_class=ModClass.IMPLICIT,
                                                mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.IMPLICIT])
        enchants = rp.fetch_tiered_mod_strings(mod_class=ModClass.ENCHANT,
                                               mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.ENCHANT])
        fractureds = rp.fetch_tiered_mod_strings(mod_class=ModClass.FRACTURED,
                                                 mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.FRACTURED])
        explicits = rp.fetch_tiered_mod_strings(mod_class=ModClass.EXPLICIT,
                                                mod_abbrev=ApiResponseParser.mod_class_to_abbrev[ModClass.EXPLICIT])

        s = []

        s.append(f"{rp.item_name} {rp.base_name}\n"
                 f"{rp.base_category}\n")

        if properties_:
            s.append('\n'.join(f"{k}: {v}" for k, v in properties_.items()))

        s.append(f"\nItem Level: {rp.ilvl}")

        if rp.level_requirement:
            s.append(f"\nRequires Level: {rp.level_requirement} ")
        if att_requirements:
            s.append(', '.join(f"{k}: {v}" for k, v in att_requirements.items()))

        skills = _SkillsFactory.create_skills(rp)
        if skills:
            s.append('\n' + '\n'.join([f"Grants Skill: Level {skill.level} {skill.name}" for skill in skills]))

        s.append('\n\n' + '\n'.join(implicits + enchants + fractureds + explicits))
        s.append(f"\n\n{rp.price.amount}x {rp.price.currency.value}  IGN: {rp.account_name}")

        return ''.join(s)

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

    @property
    def max_quality(self):
        return self._determine_max_quality()

    def set_quality(self, new_quality: int):
        self.item_properties['quality'] = new_quality

    @property
    def prefixes(self):
        return [mod for mod in self.mods if mod.affix_type == ModAffixType.PREFIX]

    def determine_open_suffixes(self) -> int:
        if self.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX])

    @property
    def open_prefixes(self) -> int:
        if self.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.PREFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.PREFIX])

    @property
    def suffixes(self):
        return [mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX]

    @property
    def open_suffixes(self) -> int:
        if self.metadata.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.metadata.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type == ModAffixType.SUFFIX])

    def fetch_mods(self, mod_class: ModClass):
        return self._mod_class_to_attribute[mod_class]
