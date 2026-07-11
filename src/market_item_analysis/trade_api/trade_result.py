import pprint
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np

from src.market_item_analysis.shared import utils as shared_utils
from src.market_item_analysis.shared.text_analysis import TextAnalyzer


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
class TradeResultSectionContext:
    listing_data: dict
    key_path: list[str]


class TradeResultSection(ABC):

    def __init__(self,
                 data,
                 key_path: list[str]):
        self.data = data
        self.key_path = key_path

    def require(self, key):
        if key not in self.data:
            raise ConfigError(message=f"Could not find required key '{key}'.",
                              key_path=self.key_path + key)

        return self.data[key]

    def optional(self, key):
        if key not in self.data:
            return None

        return self.data[key]

class TradeResultListingPriceSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.type = self.require('type')
        self.amount = self.require('amount')
        self.currency = self.require('currency')

class TradeResultListingAccountSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.is_online = self.require('online')

class TradeResultListingSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)
        self.price_section = TradeResultListingPriceSection(data=self.require('price'),
                                                            key_path=key_path + ['price'])
        self.account_section = TradeResultListingAccountSection(data=self.require('account'),
                                                                key_path=key_path + ['account'])
        self.gold_fee = self.require('fee')
        self.indexed_datetime = self.require(key='indexed')

class TradeResultItemRequirementSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = self.require('values')

class TradeResultItemPropertyValue:

    def __init__(self, data: list):
        self.values_str = data[0]
        self.value_type_id = data[1]

class TradeResultItemPropertySection(TradeResultSection):

    def __init__(self, data: list, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.values = [TradeResultItemPropertyValue(data=value_list)
                       for value_index, value_list in enumerate(self.require('values'))]

class TradeResultItemModStatMagnitudesSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.min = self.require('min')
        self.max = self.require('max')

class TradeResultItemModStatSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.name = self.require('name')
        self.tier = self.require('tier')
        self.level = self.require('level')
        self.magnitudes = [
            TradeResultItemModStatMagnitudesSection(data=magnitudes_d, key_path=key_path + [magnitudes_index])
            for magnitudes_index, magnitudes_d in enumerate(self.require('magnitudes'))
        ]

class TradeResultItemModSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.description = self.require('description')
        self.hash = self.require('hash')
        self.mod_stats = [
            TradeResultItemModStatSection(data=stats_d, key_path=key_path + [])
            for stats_d in self.require('mods')
        ]

class TradeResultItemSection(TradeResultSection):

    def __init__(self, data: dict, key_path: list[str]):
        super().__init__(data=data, key_path=key_path)

        self.verified = self.require('verified')
        self.icon_url = self.require('icon')
        self.id = self.require('id')
        self.base_type = self.require('baseType')
        self.rarity = self.require('rarity')
        self.ilvl = self.require('ilvl')

        self.is_identified = self.require('identified')
        self.is_corrupted = self.optional('corrupted')

        self.properties = [
            TradeResultItemPropertySection(data=property_d, key_path=key_path + [property_index])
            for property_index, property_d in enumerate(self.require('properties'))
        ]

        self.requirements = [
            TradeResultItemRequirementSection(data=requirement_d, key_path=key_path + [requirement_index])
            for requirement_index, requirement_d in enumerate(self.require('requirements'))
        ]

        self.implicit_mods = self._parse_mods('implicitMods')
        self.explicit_mods = self._parse_mods('explicitMods')
        self.enchant_mods = self._parse_mods('enchantMods')
        self.fractured_mods = self._parse_mods('fracturedMods')
        self.rune_mods = self._parse_mods('runeMods')

    def _parse_mods(self, key: str) -> list[TradeResultItemModSection] | None:
        """Helper that returns type-hinted list or None."""
        raw_mods = self.optional(key)
        if not raw_mods:
            return None

        return [
            TradeResultItemModSection(
                data=mod_d,
                key_path=self.key_path + [(key, str(i))]
            )
            for i, mod_d in enumerate(raw_mods)
        ]


class TradeResult(TradeResultSection):

    def __init__(self, api_response_data: dict):
        super().__init__(data=api_response_data,
                         key_path=[])
        self.raw_response_data = api_response_data.copy()
        self.data = self.preprocess(api_response_data)

        try:
            self.listing = TradeResultListingSection(data=self.require('listing'),
                                                     key_path=['listing'])
            self.item = TradeResultItemSection(data=self.require('item'),
                                               key_path=['item'])
        except ConfigError as e:
            print(f"Error caught @ {e.key_path}: {e}\n\nTrade result data:\n\n{pprint.pformat(api_response_data)}")


    def to_dict(self) -> dict:
        return self.raw_response_data

    @staticmethod
    def _clean_blank_spear_implicit(response_data: dict):
        # This currently only applies to the blank implicit mod on spears
        mods_data = response_data['item']['extended']['mods']
        if 'implicit' not in mods_data:
            return response_data

        mods_data['implicit'] = [
            mod for mod in mods_data['implicit']
            if not (
                    mod.get("name") == "" and
                    mod.get("tier") == "" and
                    mod.get("magnitudes") is None and
                    mod.get("level") == 1
            )
        ]
        return response_data

    @classmethod
    def preprocess(cls, item_data: dict) -> dict:
        # This currently only applies to the blank implicit mod on spears
        mods_data = item_data['item']['extended']['mods']
        if 'implicit' not in mods_data:
            return item_data

        mods_data['implicit'] = [
            mod for mod in mods_data['implicit']
            if not (
                    mod.get("name") == "" and
                    mod.get("tier") == "" and
                    mod.get("magnitudes") is None and
                    mod.get("level") == 1
            )
        ]

        d = cls._clean_blank_spear_implicit(raw_item_data)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "ApiResponse":
        return cls(api_response_data=d)

    def determine_elemental_damage_values(self) -> ElementalDamageValues:
        return _ElementalDamageParser.determine_elemental_damage(raw_item_data=self.item_data)

    @property
    def skills_data(self) -> dict:
        return self.item_data['grantedSkills'] if 'grantedSkills' in self.item_data else dict()

    @property
    def date_fetched(self) -> datetime:
        return shared_utils.format_date_into_utc(self._listing_data['indexed'])

    @property
    def listing_id(self) -> str:
        return self.preprocessed_data['id']

    @property
    def quality(self) -> int:
        return int(self._item_properties['quality'])

    @property
    def account_name(self) -> str:
        return self._listing_data['account']['name']

    @property
    def gold_cost(self) -> int:
        return int(self._listing_data['fee'])

    @property
    def price_currency(self) -> str:
        return self._listing_data['price']['currency']

    @property
    def price_amount(self) -> int:
        return int(self._listing_data['price']['amount'])

    @property
    def item_name(self) -> str:
        return self.item_data['name']

    @property
    def base_name(self) -> str:
        return self.item_data['baseType']

    @property
    def rarity(self) -> Rarity:
        rarity_str = self.item_data['rarity'].lower()
        return Rarity(rarity_str)

    @property
    def ilvl(self) -> int:
        return int(self.item_data['ilvl'])

    @property
    def level_requirement(self) -> int:
        reqs = self.item_data['requirements']
        return int(reqs[0]['values'][0][0]) if reqs and reqs[0]['name'] == 'Level' else 0

    @property
    def is_identified(self) -> bool:
        return 'identified' in self.item_data and self.item_data['identified'] is True

    @property
    def is_corrupted(self) -> bool:
        return 'corrupted' in self.item_data and self.item_data['corrupted'] is True

    @property
    def base_category(self) -> str:
        return self._item_properties[0]['name']

    def _extract_attribute_requirement(self, attribute_name: str):
        requirements = self.item_data['requirements']
        req = [req for req in requirements if req['name'] == attribute_name]
        return int(req[0]['values'][0][0]) if req else 0

    @property
    def strength_requirement(self) -> int:
        return self._extract_attribute_requirement('str')

    @property
    def intelligence_requirement(self) -> int:
        return self._extract_attribute_requirement('int')

    @property
    def dexterity_requirement(self) -> int:
        return self._extract_attribute_requirement('dex')
