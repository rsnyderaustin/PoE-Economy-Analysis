import pprint
from abc import ABC
from typing import Any

from src.market_item_analysis.core.enums.equipment import ModType


class ConfigError(Exception):

    def __init__(self, message: str, key_path: list[str]):
        super().__init__(message)

        self.key_path = key_path


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

    def optional(self, key, default: Any = None):
        if key not in self._data:
            return default

        return self._data[key]

class Price(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.type = self.require('type')
        self.amount = self.require('amount')
        self.currency = self.require('currency')

class Account(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.is_online = self.require('online')

class Listing(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)
        self.price = Price(data=self.require('price'),
                           key_path=key_path + ['price'])
        self.account = Account(data=self.require('account'),
                               key_path=key_path + ['account'])
        self.gold_fee = self.require('fee')
        self.indexed_datetime = self.require(key='indexed')

class Requirement(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = self.require('values')

class Skill(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = self.require('values')

class Property(Section):

    def __init__(self, data: list, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = self.require('values')

class ModMagnitude(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.min = self.require('min')
        self.max = self.require('max')

class SubMod(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.tier = self.require('tier')
        self.level = self.require('level')
        self.magnitudes = [
            ModMagnitude(data=magnitudes_d, key_path=key_path + [magnitudes_index])
            for magnitudes_index, magnitudes_d in enumerate(self.require('magnitudes'))
        ]

class Mod(Section):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.description = self.require('description')

        self.flags = self.optional('flags')
        self.hash = self.optional('hash')
        if (mods_data := self.optional('mods')) is not None:
            self.sub_mods = [SubMod(data=mod_d,
                                    key_path=key_path + ['mods', mod_index])
                             for mod_index, mod_d in enumerate(mods_data)]
        else:
            self.sub_mods = None

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

        self.is_identified = self.optional('identified')
        self.is_corrupted = self.optional('corrupted')

        if (skills_list := self.optional('grantedSkills')) is not None:
            self.skills = [
                Skill(data=skill_data,
                      key_path=['grantedSkills', f'index_{skill_index}'])
                for skill_index, skill_data in enumerate(skills_list)
            ]
        else:
            self.skills = []

        self.properties = [
            Property(data=property_d, key_path=key_path + [property_index])
            for property_index, property_d in enumerate(self.require('properties'))
        ]

        self.requirements = [
            Requirement(data=requirement_d, key_path=key_path + [requirement_index])
            for requirement_index, requirement_d in enumerate(self.require('requirements'))
        ]

        if explicit_mods := self.optional(ModType.EXPLICIT.trade_result_key) is not None:
            self.explicit_mods = [
                Mod(
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


class Result(Section):

    def __init__(self, api_response_data: dict):
        super().__init__(data=api_response_data,
                         key_path=[])
        self._data = api_response_data

        try:
            self.listing = Listing(data=self.require('listing'), key_path=['listing'])
            self.item = Item(data=self.require('item'), key_path=['item'])
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
    def from_dict(cls, d: dict) -> "Result":
        return Result(api_response_data=d)

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
