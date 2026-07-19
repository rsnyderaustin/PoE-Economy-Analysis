import re
from abc import ABC, abstractmethod

import numpy as np

import uuid
from datetime import datetime

from src.market_item_analysis.core.dictionary_service import DictionaryService
from src.market_item_analysis.core.enums.equipment import EquipmentCategory, Rarity, AttributeType, AffixType, ModType, \
    EquipmentStat, ModFlag
from src.market_item_analysis.core.enums.trade import Currency
from src.market_item_analysis.core.string_service import StringService
from src.market_item_analysis.core.types import Range
from src.market_item_analysis.trade_api import api_result


class ListingSection(ABC):

    def to_dict(self) -> dict:
        return DictionaryService.convert_to_dict(self)

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict):
        pass


class SubMod(ListingSection):

    def __init__(self,
                 name: str,
                 affix_type: AffixType,
                 tier: int,
                 level: int,
                 magnitudes: list[Range]):
        self.name = name
        self.affix_type = affix_type
        self.tier = tier
        self.level = level
        self.magnitudes = magnitudes

    @classmethod
    def from_dict(cls, d: dict) -> "SubMod":
        return SubMod(
            name=d['name'],
            affix_type=AffixType(d['affix_type']),
            tier=d['tier'],
            level=d['level'],
            magnitudes=[Range.from_dict(magnitude_d) for magnitude_d in d['magnitudes']]
        )

    @classmethod
    def from_sub_mod_result(cls, sub_mod_result: api_result.SubMod) -> "SubMod":
        return SubMod(
            name=sub_mod_result.name,
            affix_type=AffixType.from_trade_result_id(trade_result_id=sub_mod_result.tier[0]),
            tier=int(sub_mod_result.tier[1:]),
            level=int(sub_mod_result.level),
            magnitudes=[Range(min=mag_section.min, max=mag_section.max)
                        for mag_section in sub_mod_result.magnitudes]
        )

class Mod(ListingSection):

    def __init__(self,
                 description: str,
                 mod_types: list[ModType],
                 hash_id: str | None = None,
                 sub_mods: list[SubMod] | None = None,
                 affix_type: AffixType | None = None):
        self.description = description
        self.mod_types = mod_types
        self.hash_id = hash_id
        self.sub_mods = sub_mods
        self.affix_type = affix_type

    @classmethod
    def from_dict(cls, d: dict) -> "Mod":

        return Mod(
            description=d['description'],
            mod_types=[ModType(mod_type_str) for mod_type_str in d['mod_types']],
            hash_id=d.get('hash_id'),
            sub_mods=[SubMod.from_dict(sub_mod_d) for sub_mod_d in d['sub_mods']] if 'sub_mods' in d else None,
            affix_type=AffixType(d['affix_type']) if 'affix_type' in d else None
        )

    @classmethod
    def from_mod_result(cls,
                        result_mod: api_result.Mod,
                        mod_type_section: ModType) -> "Mod":
        mod_types = [mod_type_section]
        if result_mod.flags.get(ModFlag.FRACTURED.trade_result_key) is True:
            mod_types.append(ModType.FRACTURED)

        return Mod(
            description=result_mod.description,
            mod_types=mod_types,
            hash_id=result_mod.hash,
            sub_mods=[SubMod.from_sub_mod_result(sub_mod_section) for sub_mod_section in result_mod.sub_mods]
        )


class Mods(ListingSection):

    def __init__(self, mods: list[Mod]):
        self.mods = mods

    @classmethod
    def from_dict(cls, d: dict) -> "Mods":
        return Mods(
            mods=[Mod.from_dict(d=mod_dict) for mod_dict in d['mods']]
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Mods":
        explicit_mods = [Mod.from_mod_result(result_mod=explicit_mod, mod_type_section=ModType.EXPLICIT)
                         for explicit_mod in r.item.explicit_mods]
        implicit_mods = [Mod.from_mod_result(result_mod=implicit_mod, mod_type_section=ModType.IMPLICIT)
                         for implicit_mod in r.item.implicit_mods]
        enchant_mods = [Mod.from_mod_result(result_mod=enchant_mod, mod_type_section=ModType.ENCHANT)
                        for enchant_mod in r.item.enchant_mods]
        rune_mods = [Mod.from_mod_result(result_mod=rune_mod, mod_type_section=ModType.RUNE)
                     for rune_mod in r.item.rune_mods]

        return Mods(mods=explicit_mods + implicit_mods + enchant_mods + rune_mods)


class Skill(ListingSection):

    _SKILL_DESCRIPTION_RE = re.compile(r'(\d+)\s*(.*)')


    def __init__(self,
                 name: str,
                 level: int = None):
        self.name = name
        self.level = level

    @classmethod
    def from_dict(cls, d: dict) -> "Skill":
        return Skill(
            name=d['name'],
            level=int(d['level']) if d['level'] else None
        )

    @classmethod
    def from_skill_result(cls, skill_result: api_result.Skill):
        re_match = re.search(pattern=cls._SKILL_DESCRIPTION_RE,
                             string=skill_result.values[0][0])
        if re_match:
            return Skill(
                name=re_match.group(1),
                level=int(re_match.group(2))
            )
        else:
            return Skill(
                name=skill_result.values[0][0]
            )


class Metadata(ListingSection):

    def __init__(self,
                 poster_account_name: str,
                 date_posted: datetime):
        self.poster_account_name = poster_account_name
        self.date_posted = date_posted

    @classmethod
    def from_dict(cls, d: dict) -> "Metadata":
        return Metadata(
            poster_account_name=d['poster_account_name'],
            date_posted=d['date_posted']
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Metadata":
        return Metadata(
            poster_account_name=r.listing.account.name,
            date_posted=r.listing.indexed_datetime
        )


class Requirements(ListingSection):

    def __init__(self,
                 player_level: int,
                 strength: int,
                 intelligence: int,
                 dexterity: int):
        self.player_level = player_level
        self.strength = strength
        self.intelligence = intelligence
        self.dexterity = dexterity

    @classmethod
    def from_dict(cls, d: dict) -> "Requirements":
        return Requirements(
            player_level=int(d['player_level']),
            strength=int(d['strength']),
            intelligence=int(d['intelligence']),
            dexterity=int(d['dexterity'])
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Requirements":
        return Requirements(
            player_level=r.item.requirements.level_requirement,
            strength=r.item.requirements.strength_requirement,
            intelligence=r.item.requirements.intelligence_requirement,
            dexterity=r.item.requirements.dexterity_requirement
        )


class Skills(ListingSection):

    def __init__(self,
                 skills: list[Skill]):
        self.skills = skills

    @classmethod
    def from_dict(cls, d: dict) -> "Skills":
        return cls([Skill.from_dict(skill_d) for skill_d in d['skills']])

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Skills":
        skills = [Skill.from_skill_result(result_skill) for result_skill in r.item.skills]
        return Skills(skills)


class EquipmentType(ListingSection):

    _wand_btype_map = {
        'volatile_wand': 'fire_wand',
        'withered_wand': 'chaos_wand',
        'bone_wand': 'physical_wand',
        'frigid_wand': 'cold_wand',
        'galvanic_wand': 'lightning_wand',
    }

    def __init__(self,
                 attribute_types: list[AttributeType],
                 category: EquipmentCategory):
        self.attribute_types = attribute_types
        self.category = category

    @classmethod
    def from_dict(cls, d: dict):
        return EquipmentType(
            attribute_types=[AttributeType(s) for s in d['attribute_types']],
            category=EquipmentCategory[d['category']]
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "EquipmentType":
        category = EquipmentCategory.from_trade_result_id(r.item.equipment_category_id)
        attribute_types = [AttributeType.from_trade_result_id(requirement.name) for requirement in r.item.equipment_requirements]

        return EquipmentType(attribute_types=attribute_types, category=category)

class Price(ListingSection):

    def __init__(self,
                 currency: Currency,
                 currency_amount: int,
                 gold_cost: int):
        self.currency = currency
        self.currency_amount = currency_amount
        self.gold_cost = gold_cost

    @classmethod
    def from_dict(cls, d: dict) -> "Price":
        return Price(
            currency=Currency(d['currency']),
            currency_amount=int(d['currency_amount']),
            gold_cost=int(d['gold_cost'])
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Price":
        return Price(
            currency=Currency(r.listing.price.currency),
            currency_amount=int(r.listing.price.amount),
            gold_cost=int(r.listing.price.gold_cost)
        )


class Stat(ListingSection):

    def __init__(self, stat: EquipmentStat, value: int | float | Range):
        self.stat = stat
        self.value = value

    _TYPE_REGISTRY = {
        "Range": Range.from_dict,
        "int": int,
        "float": float,
    }
    
    @classmethod
    def from_dict(cls, d: dict) -> "Stat":
        # 2. Look up the builder in the dictionary
        builder = cls._TYPE_REGISTRY.get(d['_value_type'])

        if not builder:
            raise ValueError(f"Unknown value type: {d['_value_type']}")

        return Stat(
            stat=EquipmentStat[d['stat']],
            value=builder(d['value'])  # Call the builder function
        )

class Stats(ListingSection):

    def __init__(self, stats: list[Stat]):
        self.stats = stats

    @classmethod
    def from_dict(cls, d: dict) -> "Stats":
        stats = [Stat.from_dict(d=stat_d) for stat_d in d['stats']]
        return Stats(stats=stats)

    @classmethod
    def _resolve_value(cls, value_str: str) -> int | float | Range:
        extracted_obj = StringService.extract_numbers(value_str)

        numbers = extracted_obj.numbers
        if len(numbers) == 1:
            return numbers[0]
        elif len(numbers) == 2:
            return Range(min=numbers[0], max=numbers[1])
        else:
            raise ValueError(f"Unable to resolve item property string value: {value_str}")

    _ELEMENTAL_DAMAGE_VALUE_ID_MAP = {
        4: EquipmentStat.FIRE_DAMAGE,
        5: EquipmentStat.COLD_DAMAGE,
        6: EquipmentStat.LIGHTNING_DAMAGE
    }
    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Stats":
        stats = []
        for p in r.item.properties:
            stat_enum = EquipmentStat.from_trade_result_id(trade_result_id=p.name)

            if stat_enum == EquipmentStat.ELEMENTAL_DAMAGE:
                for property_value in p.values:
                    value_stat_enum = cls._ELEMENTAL_DAMAGE_VALUE_ID_MAP[property_value.value_type_id]
                    value = cls._resolve_value(value_str=property_value.values_str)
                    stats.append(Stat(stat=value_stat_enum, value=value))
            else:
                stats.append(
                    Stat(stat=stat_enum, value=cls._resolve_value(p.values[0].values_str))
                )

        return Stats(stats=stats)



class ItemAttributes(ListingSection):

    def __init__(self,
                 rarity: Rarity,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 quality: int):
        self.rarity = rarity
        self.ilvl = ilvl
        self.identified = identified
        self.corrupted = corrupted
        self.quality = quality

    @classmethod
    def from_dict(cls, d: dict) -> "ItemAttributes":
        rarity = Rarity(d.pop('rarity'))
        ilvl = int(d.pop('ilvl'))
        identified = bool(d.pop('identified'))
        corrupted = bool(d.pop('corrupted'))
        quality = int(d.pop('quality'))
        
        return ItemAttributes(
            rarity=rarity,
            ilvl=ilvl,
            identified=identified,
            corrupted=corrupted,
            quality=quality
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "ItemAttributes":
        return ItemAttributes(
            rarity=Rarity(r.item.rarity),
            ilvl=int(r.item.ilvl),
            identified=bool(r.item.identified),
            corrupted=bool(r.item.corrupted),
            quality=int(r.item.quality)
        )


class Item(ListingSection):

    def __init__(self,
                 flavor_name: str,
                 category: EquipmentCategory,
                 requirements: Requirements,
                 stats: Stats,
                 mods: Mods,
                 skills: Skills,
                 item_attributes: ItemAttributes,
                 internal_id: str = None):
        self.flavor_name = flavor_name
        self.category = category
        self.requirements = requirements
        self.stats = stats
        self.mods = mods
        self.skills = skills
        self.item_attributes = item_attributes

        self.internal_id = internal_id or uuid.uuid4().hex

    def __key(self):
        return [
            self.flavor_name,
            self.stats.to_dict(),
            self.mods.to_dict()
        ]

    def __hash__(self):
        return hash(self.__key())

    @classmethod
    def from_dict(cls, d: dict) -> "Item":
        return Item(
            flavor_name=d['flavor_name'],
            category=EquipmentCategory(d['category']),
            requirements=Requirements.from_dict(d['requirements']),
            stats=Stats.from_dict(d['stats']),
            mods=Mods.from_dict(d['mods']),
            skills=Skills.from_dict(d['skills']),
            item_attributes=ItemAttributes.from_dict(d['item_attributes']),
            internal_id=d['internal_id']
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Item":
        return Item(
            flavor_name=r.item.flavor_name,
            category=EquipmentCategory.from_trade_result_id(trade_result_id=r.item.equipment_category_id) if r.item.equipment_category_id else None,
            requirements=Requirements.from_trade_api_result(r),
            stats=Stats.from_trade_api_result(r),
            mods=Mods.from_trade_api_result(r),
            skills=Skills.from_trade_api_result(r),
            item_attributes=ItemAttributes.from_trade_api_result(r),
        )


class Listing(ListingSection):

    def __init__(self,
                 metadata: Metadata,
                 price: Price,
                 item: Item):
        self.metadata = metadata
        self.price = price
        self.item = item


    @classmethod
    def from_dict(cls, d: dict) -> "Listing":
        return Listing(
            metadata=Metadata.from_dict(d['metadata']),
            price=Price.from_dict(d['price']),
            item=Item.from_dict(d['item'])
        )

    @classmethod
    def from_trade_api_result(cls, r: api_result.Result) -> "Listing":
        return Listing(
            metadata=Metadata.from_trade_api_result(r),
            price=Price.from_trade_api_result(r),
            item=Item.from_trade_api_result(r)
        )

