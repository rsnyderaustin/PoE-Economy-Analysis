import pprint
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from src.market_item_analysis.instances_and_definitions import ItemMod
from src.market_item_analysis.instances_and_definitions.item_instances import ItemMods
from src.market_item_analysis.program_logging import LogsHandler, LogFile
from src.market_item_analysis.shared import utils
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Currency, Rarity
from src.market_item_analysis.text_analysis.analyzers import ModTextAnalyzer
from src.market_item_analysis.shared import utils as shared_utils

parse_log = LogsHandler().fetch_log(LogFile.API_PARSING)


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
        4: 'fire_damage',
        5: 'cold_damage',
        6: 'lightning_damage'
    }

    @classmethod
    def _determine_elemental_type(cls, raw_id: int) -> str:
        return cls._elemental_id_map[raw_id]

    @classmethod
    def determine_elemental_damage(cls, raw_item_data: dict) -> ElementalDamageValues:
        raw_properties = raw_item_data['properties'][1:]

        elemental_properties = [p for p in raw_properties if p['name'] == 'elemental_damage']
        if len(elemental_properties) >= 2:
            raise ValueError(f"Unexpectedly got {len(elemental_properties)} elemental properties keys. Expected 0 or 1."
                             f"\n\n--- Raw item data: {pprint.pformat(raw_item_data)} ---")

        properties_list = elemental_properties[0]['value']
        values = ElementalDamageValues()
        for ele_property in properties_list:
            elemental_type = cls._determine_elemental_type(ele_property[1])
            values = ModTextAnalyzer.extract_values(ele_property[0])
            values.add_damage_value(elemental_type=elemental_type,
                                    value=np.average(values))

        return values


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
        self.raw_response_data = _ApiResponsePreprocessor.preprocess(api_response_data)

        self.item_data = self.raw_response_data['item']
        self._item_properties = self.item_data['properties']
        self._listing_data = self.raw_response_data['listing']

    def determine_elemental_damage_values(self) -> ElementalDamageValues:
        return _ElementalDamageParser.determine_elemental_damage(raw_item_data=self.item_data)

    def fetch_sub_mod_hash_to_text(self, mod_class: ModClass) -> dict:
        return self.sub_mod_hash_to_text[mod_class] if mod_class in self.sub_mod_hash_to_text else dict()

    @property
    def skills_data(self) -> dict:
        return self.item_data['grantedSkills'] if 'grantedSkills' in self.item_data else dict()

    @property
    def date_fetched(self) -> datetime:
        return shared_utils.format_date_into_utc(self._listing_data['indexed'])

    @property
    def listing_id(self) -> str:
        return self.raw_response_data['id']

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
        return shared_utils._extract_from_brackets(self._item_properties[0]['name'])

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
