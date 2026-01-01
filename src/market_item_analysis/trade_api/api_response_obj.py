import pprint
from datetime import datetime

import numpy as np

from src.market_item_analysis.shared import utils as shared_utils
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Rarity
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


class _ApiResponsePreprocessor:

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
    def preprocess(cls, raw_item_data: dict) -> dict:
        d = cls._clean_blank_spear_implicit(raw_item_data)
        return d


class ApiResponse:

    def __init__(self, api_response_data: dict):
        self.raw_response_data = api_response_data.copy()
        self.preprocessed_data = _ApiResponsePreprocessor.preprocess(api_response_data)

        self.item_data = self.preprocessed_data['item']
        self._item_properties = self.item_data['properties']
        self._listing_data = self.preprocessed_data['listing']

    def to_dict(self) -> dict:
        return self.preprocessed_data

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
