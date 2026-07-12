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
from src.market_item_analysis.trade_api.raw_result import TradeApiResult, TradeApiResultItemModSection, \
    TradeApiResultItemModStatSection


class TradeApiResultObject(ABC):

    def to_dict(self) -> dict:
        return DictionaryService.convert_to_dict(self)

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict):
        pass


class ItemSubMod:

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
    def from_dict(cls, d: dict) -> "ItemSubMod":
        return ItemSubMod(
            name=d['name'],
            affix_type=AffixType(d['affix_type']),
            tier=d['tier'],
            level=d['level'],
            magnitudes=[Range.from_dict(magnitude_d) for magnitude_d in d['magnitudes']]
        )

    @classmethod
    def from_trade_api_result(cls, trade_api_sub_mod_section: TradeApiResultItemModStatSection) -> "ItemSubMod":
        return ItemSubMod(
            name=trade_api_sub_mod_section.name,
            affix_type=AffixType.from_trade_result_id(trade_result_id=trade_api_sub_mod_section.tier[0]),
            tier=int(trade_api_sub_mod_section.tier[1:]),
            level=int(trade_api_sub_mod_section.level),
            magnitudes=[Range(min=mag_section.min, max=mag_section.max)
                        for mag_section in trade_api_sub_mod_section.magnitudes]
        )

class ItemMod:

    def __init__(self,
                 description: str,
                 mod_types: list[ModType],
                 hash_id: str | None = None,
                 sub_mods: list[ItemSubMod] | None = None,
                 affix_type: AffixType | None = None):
        self.description = description
        self.mod_types = mod_types
        self.hash_id = hash_id
        self.sub_mods = sub_mods
        self.affix_type = affix_type

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMod":

        return ItemMod(
            description=d['description'],
            mod_types=[ModType(mod_type_str) for mod_type_str in d['mod_types']],
            hash_id=d.get('hash_id'),
            sub_mods=[ItemSubMod.from_dict(sub_mod_d) for sub_mod_d in d['sub_mods']] if 'sub_mods' in d else None,
            affix_type=AffixType(d['affix_type']) if 'affix_type' in d else None
        )

    @classmethod
    def from_trade_api_result(cls,
                              trade_api_mod_section: TradeApiResultItemModSection,
                              mod_type_section: ModType) -> "ItemMod":
        mod_types = [mod_type_section]
        if trade_api_mod_section.flags.get(ModFlag.FRACTURED.trade_result_key) is True:
            mod_types.append(ModType.FRACTURED)

        return ItemMod(
            description=trade_api_mod_section.description,
            mod_types=mod_types,
            hash_id=trade_api_mod_section.hash,
            sub_mods=[ItemSubMod.from_trade_api_result(sub_mod_section) for sub_mod_section in trade_api_mod_section.sub_mods]
        )


class EquipmentSkill(TradeApiResultObject):

    def __init__(self,
                 name: str,
                 level: int = None):
        self.name = name
        self.level = level or 1

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentSkill":
        return cls(**d)


class ListingMetadata(TradeApiResultObject):

    def __init__(self,
                 poster_account_name: str,
                 date_posted: datetime):
        self.poster_account_name = poster_account_name
        self.date_posted = date_posted

    @classmethod
    def from_dict(cls, d: dict) -> "ListingMetadata":
        return ListingMetadata(
            poster_account_name=d['poster_account_name'],
            date_posted=d['date_posted']
        )

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "ListingMetadata":
        return ListingMetadata(
            poster_account_name=r.listing.account.name,
            date_posted=r.listing.indexed_datetime
        )


class EquipmentRequirements(TradeApiResultObject):

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
    def from_dict(cls, d: dict) -> "EquipmentRequirements":
        return cls(**d)

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "EquipmentRequirements":
        return EquipmentRequirements(
            player_level=r.item.requirements.level_requirement,
            strength=r.item.requirements.strength_requirement,
            intelligence=r.item.requirements.intelligence_requirement,
            dexterity=r.item.requirements.dexterity_requirement
        )


class EquipmentSkills(TradeApiResultObject):

    def __init__(self,
                 skills: list[EquipmentSkill]):
        self.skills = skills

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentSkills":
        return cls([EquipmentSkill.from_dict(skill_d) for skill_d in d['skills']])

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "EquipmentSkills":
        if not r.item.skills:
            return EquipmentSkills(skills=[])

        skills = []
        for skill_data in r.skills_data:
            raw_skill = skill_data['values'][0]

            # Spear Throw is the only skill that is granted by an item without a level. May have to update in the future
            if raw_skill[0] == 'Spear Throw':
                new_skill = EquipmentSkill(
                    name='Spear Throw'
                )
                skills.append(new_skill)
                continue

            if isinstance(raw_skill, str):
                _, level_str, *skill_parts = raw_skill.split()
                level = int(level_str)
                skill_name = ' '.join(skill_parts)
            else:
                skill_name = raw_skill[0][0]
                level = raw_skill[0][1]

            new_skill = EquipmentSkill(
                name=skill_name,
                level=level
            )

            skills.append(new_skill)

        return EquipmentSkills(skills=skills)


class EquipmentType(TradeApiResultObject):

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
        attribute_types = [AttributeType.from_dict(type_d) for type_d in d['attribute_types']]
        category = EquipmentCategory.from_dict(d['category'])

        return EquipmentType(
            attribute_types=attribute_types,
            category=category
        )

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "EquipmentType":
        category = EquipmentCategory.from_trade_result_id(r.item.equipment_category_id)
        attribute_types = [AttributeType.from_trade_result_id(requirement.name) for requirement in r.item.equipment_requirements]

        return EquipmentType(attribute_types=attribute_types, category=category)

class ItemMods(TradeApiResultObject):

    def __init__(self,
                 mods: list[ItemMod]):
        self.mods = mods

    @classmethod
    def from_dict(cls, d: dict) -> "ItemMods":
        mods = []
        for mod_type_str, mod_dicts in d.items():
            mod_type = ModType[mod_type_str]
            for mod_dict in mod_dicts:
                new_mod = ItemMod.from_dict(d=mod_dict, mod_type_section=mod_type)
                mods.append(new_mod)

        return ItemMods(mods=mods)

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "ItemMods":
        mods = []
        for explicit_mod_section in r.item.explicit_mods:
            new_mod = ItemMod(

            )

        implicit_mods = [ItemMod(description=mod_desc, mod_types=[ModType.IMPLICIT]) for mod_desc in r.item.implicit_mod_descriptions]
        enchant_mods = [ItemMod(description=mod_desc, mod_types=[ModType.ENCHANT]) for mod_desc in r.item.enchant_mod_descriptions]
        rune_mods = [ItemMod(description=mod_desc, mod_types=[ModType.RUNE]) for mod_desc in r.item.rune_mod_descriptions]

        explicit_mods = [ItemMod.from_dict() for explicit_mod_d in r.item.explicit_mods]

        mods_d = {
            ModType.IMPLICIT: [],
            ModType.ENCHANT: [],
            ModType.FRACTURED: [],
            ModType.EXPLICIT: [],
            ModType.RUNE: []
        }
        explicit_mods =
        for mod_type_member in ModType.__members__.values():

            if mod_class.trade_result_key not in r.item.:
                continue

            mod_dicts = r.item_data[mod_class.api_key]
            new_mods = [ItemMod(description=mod_text,
                                mod_class=mod_class) for mod_text in mod_dicts]

            mods_d[mod_class].extend(new_mods)

        item_mods = ItemMods(mods_d=mods_d)
        return item_mods

    @property
    def all_mods(self) -> list[ItemMod]:
        return [m
                for mods_list in self._mods_d.values()
                for m in mods_list]

    def add_mod(self, mod: ItemMod):
        self._mods_d[mod.mod_class].append(mod)

    def fetch_mods_by_class(self, mod_class: ModClass) -> list[ItemMod]:
        return self._mods_d[mod_class]


class EquipmentPrice(TradeApiResultObject):

    def __init__(self,
                 currency: Currency,
                 currency_amount: int,
                 gold_cost: int):
        self.currency = currency
        self.currency_amount = currency_amount
        self.gold_cost = gold_cost

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentPrice":
        return EquipmentPrice(
            currency=Currency(d['currency']),
            currency_amount=int(d['currency_amount']),
            gold_cost=int(d['gold_cost'])
        )

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "EquipmentPrice":
        return EquipmentPrice(
            currency=Currency(r.listing.price.currency),
            currency_amount=r.listing.price.amount,
            gold_cost=r.listing.price.gold_cost
        )


class EquipmentStats(TradeApiResultObject):

    def __init__(self, stats_d: dict[EquipmentStat, [int | float | Range]]):
        self._stats_d = stats_d

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentStats":
        stats_d = dict()

        for enum_name, raw_value in d.items():
            enum_key = EquipmentStat[enum_name]
            val = Range(raw_value[0], raw_value[1]) if isinstance(raw_value, list) else raw_value

            stats_d[enum_key] = val

        return cls(stats_d)

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
    def from_trade_api_result(cls, r: TradeApiResult) -> "EquipmentStats":
        stats_d = dict()
        for p in r.item.properties:
            stat_enum = EquipmentStat.from_trade_result_id(trade_result_id=p.name)

            if stat_enum == EquipmentStat.ELEMENTAL_DAMAGE:
                for property_value in p.values:
                    value_stat_enum = cls._ELEMENTAL_DAMAGE_VALUE_ID_MAP[property_value.value_type_id]
                    value = cls._resolve_value(value_str=property_value.values_str)
                    stats_d[value_stat_enum] = value
            else:
                stats_d[stat_enum] = cls._resolve_value(p.values[0].values_str)

        return EquipmentStats(stats_d=stats_d)



class EquipmentProperties(TradeApiResultObject):

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

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentProperties":
        d['rarity'] = Rarity(d['rarity'])
        d['identified'] = bool(d['identified'])
        d['corrupted'] = bool(d['corrupted'])

        for k, v in d['additional_properties'].items():
            d[k] = v

        del d['additional_properties']

        return cls(**d)


class EquipmentListing(TradeApiResultObject):

    def __init__(self,
                 flavor_name: str,
                 metadata: ListingMetadata,
                 price: EquipmentPrice,
                 category: EquipmentCategory,
                 requirements: EquipmentRequirements,
                 stats: EquipmentStats,
                 mods_: ItemMods,
                 skills: list[EquipmentSkill],
                 properties: EquipmentProperties,
                 internal_id: str = None
                 ):
        self.flavor_name = flavor_name
        self.metadata = metadata
        self.price = price
        self.category = category
        self.requirements = requirements
        self.stats = stats
        self.mods_ = mods_
        self.skills = skills
        self.properties = properties

        self.internal_id = internal_id or uuid.uuid4().hex

    def __key(self):
        return self.metadata.listing_id

    def __hash__(self):
        return hash(self.__key())

    @classmethod
    def from_dict(cls, d: dict) -> "EquipmentListing":
        d['metadata'] = ListingMetadata.from_dict(d['metadata'])
        d['price'] = EquipmentPrice.from_dict(d['price'])
        d['namespace'] = EquipmentNamespace.from_dict(d['namespace'])
        d['types'] = ItemTypes.from_dict(d['types'])
        d['requirements'] = EquipmentRequirements.from_dict(d['requirements'])
        d['mods'] = ItemMods.from_dict(d['mods'])
        d['skills'] = [EquipmentSkill.from_dict(s) for s in d['skills']]
        d['properties'] = EquipmentProperties.from_dict(d['properties'])
        return cls(**d)

    @classmethod
    def from_trade_api_result(cls, r: TradeApiResult) -> "EquipmentListing":
        return cls(
            flavor_name=r.item.flavor_name,
            metadata=ListingMetadata.from_trade_api_result(r),
            price=EquipmentPrice.from_trade_api_result(r),
            category=EquipmentCategory.from_trade_result_id(trade_result_id=r.item.equipment_category_id) if r.item.equipment_category_id else None,
            requirements=EquipmentRequirements.from_trade_api_result(r),
            stats=ItemStats.from_trade_api_result(r),
            mods_=ItemMods.from_trade_api_result(r),
            skills=EquipmentSkill.from_trade_api_result(r),
            properties=EquipmentProperties.from_trade_api_result(r),
        )

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


