import pprint
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np

from src.market_item_analysis.core import utils as shared_utils
from src.market_item_analysis.core.dictionary_service import DictionaryService
from src.market_item_analysis.core.enums.equipment import EquipmentCategory, ModType
from src.market_item_analysis.core.string_service import TextAnalyzer, StringService
from src.market_item_analysis.core.types import Range


class ElementalDamageValues:

    def __init__(self,
                 fire: float | None = None,
                 cold: float | None = None,
                 lightning: float | None = None):
        self.fire = fire
        self.cold = cold
        self.lightning = lightning

    def add_damage_value(self, elemental_type: str, value: float):
        match elemental_type:
            case 'fire_damage':
                self.fire = value
            case 'cold_damage':
                self.cold = value
            case 'lightning_damage':
                self.lightning = value

class _ElementalDamageParser:
    _elemental_id_map = {
        4: 'Fire Damage',
        5: 'Cold Damage',
        6: 'Lightning Damage'
    }

    @classmethod
    def _determine_elemental_type(cls, raw_id: int) -> str:
        return cls._elemental_id_map[raw_id]

    @classmethod
    def determine_elemental_damage(cls, raw_item_data: dict) -> ElementalDamageValues:
        raw_properties = raw_item_data['properties']
        damage_values = ElementalDamageValues()

        singular_elemental_damage = [d for d in raw_properties
                                     if d['name'] in {'Fire Damage', 'Cold Damage', 'Lightning Damage'}]
        for elemental_damage_d in singular_elemental_damage:
            name = elemental_damage_d['name']
            val = np.mean(TextAnalyzer.extract_numbers_from_string(elemental_damage_d['values'][0]))
            damage_values.add_damage_value(elemental_type=name,
                                           value=val)

        generic_elemental_properties = [p for p in raw_properties if p['name'] == 'elemental_damage']
        if len(generic_elemental_properties) >= 2:
            raise ValueError(f"Unexpectedly got {len(generic_elemental_properties)} elemental properties keys. Expected 0 or 1."
                             f"\n\n--- Raw item data: {pprint.pformat(raw_item_data)} ---")

        properties_list = generic_elemental_properties[0]['value']
        for ele_property in properties_list:
            elemental_type = cls._determine_elemental_type(ele_property[1])
            val = np.mean(TextAnalyzer.extract_numbers_from_string(ele_property[0]))
            damage_values.add_damage_value(elemental_type=elemental_type,
                                           value=val)

        return damage_values


class ConfigError(Exception):

    def __init__(self, message: str, key_path: list[str]):
        super().__init__(message)

        self.key_path = key_path


@dataclass(frozen=True)
class SectionContext:
    listing_data: dict
    key_path: list[str]


class Section(ABC):

    def __init__(self,
                 data,
                 key_path: list[str]):
        self._data = data
        self.key_path = key_path

    def require(self, key):
        if key not in self._data:
            raise ConfigError(message=f"Could not find required key '{key}'.",
                              key_path=self.key_path + key)

        return self._data[key]

    def optional(self, key):
        if key not in self._data:
            return None

        return self._data[key]

class ListingPrice(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.type = self.require('type')
        self.amount = self.require('amount')
        self.currency = self.require('currency')

class ListingAccount(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.is_online = self.require('online')

class Listing(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)
        self.price = ListingPriceSection(data=self.require('price'),
                                                       key_path=key_path + ['price'])
        self.account = ListingAccountSection(data=self.require('account'),
                                                           key_path=key_path + ['account'])
        self.gold_fee = self.require('fee')
        self.indexed_datetime = self.require(key='indexed')

class ItemRequirement(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = self.require('values')

class ItemPropertyValue:

    def __init__(self, data: list):
        self.values_str = data[0]
        self.value_type_id = data[1]


class ItemSkill(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        

class ItemProperty(Section):

    def __init__(self, data: list, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = [ItemPropertyValue(data=value_list)
                       for value_index, value_list in enumerate(self.require('values'))]

class ModMagnitude(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.min = self.require('min')
        self.max = self.require('max')

class ItemSubMod(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.tier = self.require('tier')
        self.level = self.require('level')
        self.magnitudes = [
            ModMagnitude(data=magnitudes_d, key_path=key_path + [magnitudes_index])
            for magnitudes_index, magnitudes_d in enumerate(self.require('magnitudes'))
        ]


class ItemMod(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.description = self.require('description')

        self.flags = self.optional('flags')
        self.hash = self.optional('hash')
        if mods_data := self.optional('mods'):
            self.sub_mods = [ItemSubMod(data=mod_d,
                                        key_path=key_path + ['mods', mod_index])
                             for mod_index, mod_d in enumerate(mods_data)]
        else:
            self.sub_mods = []

class Item(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.verified = self.require('verified')
        self.icon_url = self.require('icon')
        self.id = self.require('id')
        self.flavor_name = self.require('name')
        self.type_line = self.require('typeLine')
        self.rarity = self.require('rarity')
        self.ilvl = self.require('ilvl')

        self.is_identified = self.require('identified')
        self.is_corrupted = self.optional('corrupted')

        self.skills = [
            Skills()
        ]

        self.properties = [
            ItemPropertySection(data=property_d, key_path=key_path + [property_index])
            for property_index, property_d in enumerate(self.require('properties'))
        ]

        self.requirements = [
            ItemRequirementSection(data=requirement_d, key_path=key_path + [requirement_index])
            for requirement_index, requirement_d in enumerate(self.require('requirements'))
        ]

        if explicit_mods := self.optional(ModType.EXPLICIT.trade_result_key) is not None:
            self.explicit_mods = [
                ItemModSection(
                    data=mod_d,
                    key_path=self.key_path + [(ModType.EXPLICIT.trade_result_key, str(i))]
                )
                for i, mod_d in enumerate(explicit_mods)
            ]
        else:
            self.explicit_mods = []

        self.implicit_mod_descriptions = [mod_description for mod_description in data.get(ModType.IMPLICIT.trade_result_key, [])]
        self.enchant_mod_descriptions = [mod_description for mod_description in data.get(ModType.ENCHANT.trade_result_key, [])]
        self.rune_mod_descriptions = [mod_description for mod_description in data.get(ModType.RUNE.trade_result_key, [])]

    @property
    def equipment_category_id(self) -> str | None:
        if not self.properties:
            return None

        return self.properties[0].name


class (Section):

    def __init__(self, api_response_data: dict):
        super().__init__(data=api_response_data,
                         key_path=[])
        self._data = api_response_data

        try:
            self.listing = ListingSection(data=self.require('listing'),
                                                        key_path=['listing'])
            self.item = ItemSection(data=self.require('item'),
                                                  key_path=['item'])
        except ConfigError as e:
            print(f"Error caught @ {e.key_path}: {e}\n\nTrade result data:\n\n{pprint.pformat(api_response_data)}")

    @property
    def _key(self):
        return self.item.id, self.listing.indexed_datetime

    def __hash__(self):
        return hash(self._key)

    def to_dict(self) -> dict:
        return self._data

    @classmethod
    def from_dict(cls, d: dict) -> "ApiResponse":
        return cls(api_response_data=d)

    def to_training_results_model(self) -> dict:
        return {
            "account_name": self.listing.account,
            "indexed_datetime_utc": self.listing.indexed_datetime,
            "price_currency": self.listing.price.currency,
            "price_amount": self.listing.price.amount,
            "gold_cost": self.listing.gold_fee,
            "ilvl": self.item.ilvl,
            "rarity": self.item.rarity,
            "result_object": self._data
        }
