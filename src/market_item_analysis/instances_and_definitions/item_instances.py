import datetime
import uuid

from src.market_item_analysis.data_handling import utils
from src.market_item_analysis.shared.enums.item_enums import AffixType, EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Rarity, Currency


class ItemMod:

    def __init__(self,
                 mod_text: str,
                 mod_class: ModClass):
        self.mod_text = mod_text
        self.mod_class = mod_class

    @property
    def is_hybrid(self):
        return len(self.mod_ids) >= 2


class ItemSkill:

    def __init__(self,
                 name: str,
                 level: int = None):
        self.name = name
        self.level = level or 1


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

    def add_mod(self, mod: ItemMod):
        mods = self._mod_class_d[mod.mod_class]
        mods.append(mod)

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
                 currency_amount: int,
                 gold_cost: int):
        self.currency = currency
        self.currency_amount = currency_amount
        self.gold_cost = gold_cost


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
                 internal_id: str = None
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
        s.append(f"\n\n{rp.price.currency_amount}x {rp.price.currency.value}  IGN: {rp.account_name}")

        return ''.join(s)

    @property
    def minutes_since_listed(self):
        return utils.determine_minutes_since(
            relevant_date=self.metadata.date_fetched
        )

    @property
    def minutes_since_league_start(self):
        return utils.determine_minutes_since(
            relevant_date=utils.league_start_date,
            later_date=self.metadata.date_fetched
        )

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
        return [mod for mod in self.mods if mod.affix_type == AffixType.PREFIX]

    def determine_open_suffixes(self) -> int:
        item_mods = self.mods_.all_mods
        if self.properties.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.properties.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in item_mods if mod.affix_type == AffixType.SUFFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type == AffixType.SUFFIX])

    @property
    def open_prefixes(self) -> int:
        if self.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type == AffixType.PREFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type == AffixType.PREFIX])

    @property
    def suffixes(self):
        return [mod for mod in self.mods if mod.affix_type == AffixType.SUFFIX]

    @property
    def open_suffixes(self) -> int:
        if self.metadata.rarity in [Rarity.NORMAL, Rarity.UNIQUE]:
            return 0
        elif self.metadata.rarity == Rarity.MAGIC:
            return 2 - len([mod for mod in self.mods if mod.affix_type == AffixType.SUFFIX])
        else:
            return 3 - len([mod for mod in self.mods if mod.affix_type == AffixType.SUFFIX])

    def fetch_mods(self, mod_class: ModClass):
        return self._mod_class_to_attribute[mod_class]
