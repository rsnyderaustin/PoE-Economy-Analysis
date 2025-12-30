import pprint
from dataclasses import dataclass
from datetime import datetime

from src.market_item_analysis.instances_and_definitions import ItemMod
from src.market_item_analysis.program_logging import LogsHandler, LogFile
from src.market_item_analysis.shared import shared_utils
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Currency, Rarity

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
            value = shared_utils.extract_average_from_text(ele_property[0])
            values.add_damage_value(elemental_type=elemental_type,
                                    value=value)

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


class _ModFactory:

    _mod_abbrev_d = {
        ModClass.IMPLICIT: 'implicit',
        ModClass.ENCHANT: 'enchant',
        ModClass.EXPLICIT: 'explicit',
        ModClass.FRACTURED: 'fractured',
        ModClass.RUNE: 'rune'
    }

    def __init__(self):
        self._item_data = None

    def _determine_mod_id_order(self, mod_class: ModClass) -> list[str]:
        mod_abbrev = self._mod_abbrev_d[mod_class]
        if mod_abbrev not in self._item_data['extended']['hashes']:
            return []



    def create_mods(self, item_data: dict) -> list[ItemMod]:
        self._item_data = item_data

    def _map_mod_id_to_text(self, item_data: dict) -> dict:
        self._item_data = item_data
        mod_classes = [e for e in ModClass if e != ModClass.RUNE]

        mod_id_to_text = dict()
        for mod_class in mod_classes:
            mod_abbrev = cls._mod_abbrev_d[mod_class]

            if mod_abbrev not in item_data['extended']['hashes']:
                continue

            mod_ids_list = item_data['extended']['hashes'][mod_abbrev]

            mod_id_display_order = [mod_id_item[0] for mod_id_item in mod_ids_list]
            mod_text_display_order = item_data[mod_class.value]

            mod_id_to_text = {
                mod_id: mod_text
                for mod_id, mod_text in zip(mod_id_display_order, mod_text_display_order)
            }
            mod_id_to_text[mod_class] = mod_id_to_text

        return mod_id_to_text

    def fetch_tiered_mod_strings(self, mod_class: ModClass, mod_abbrev: str) -> list[str]:
        hash_to_text = {k: f"({mod_class.value}) {v}   " for k, v in self.sub_mod_hash_to_text[mod_class].items()}
        for mod in self._item_data['extended']['mods'][mod_abbrev]:
            hashes = [magnitude['hash'] for magnitude in mod['magnitudes']]
            is_hybrid = len(hashes) >= 2

            mod_tier = f"Hybrid {mod['tier']}" if is_hybrid else mod['tier']

            # Implicit mods and enchant mods do not have a mod tier
            if not mod_tier:
                continue

            for hash_ in hashes:
                hash_to_text[hash_] = f"{hash_to_text[hash_]} {mod_tier}"

        return list(hash_to_text.values())


class ApiResponseParser:

    def __init__(self, api_response_data: dict):
        self.raw_response_data = _ApiResponsePreprocessor.preprocess(api_response_data)

        self._item_data = self.raw_response_data['item']
        self._item_properties = self._item_data['properties']
        self._listing_data = self.raw_response_data['listing']

    def elemental_damage_values(self) -> ElementalDamageValues:
        return _ElementalDamageParser.determine_elemental_damage(raw_item_data=self._item_data)

    def fetch_sub_mod_hash_to_text(self, mod_class: ModClass) -> dict:
        return self.sub_mod_hash_to_text[mod_class] if mod_class in self.sub_mod_hash_to_text else dict()

    @property
    def skills_data(self) -> dict:
        return self._item_data['grantedSkills'] if 'grantedSkills' in self._item_data else dict()

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
    def mod_classes(self) -> list[ModClass]:
        # We aren't messing with runes right now
        return [mod_class for mod_class in ModClass
                if mod_class.value in self._item_data and mod_class != ModClass.RUNE]

    def fetch_mods_data(self, mod_class: ModClass) -> dict:
        abbrev_class = self.__class__.mod_class_to_abbrev[mod_class]
        mods_data = self._item_data['extended']['mods']
        return mods_data[abbrev_class] if abbrev_class in mods_data else dict()

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
        return self._item_data['name']

    @property
    def base_name(self) -> str:
        return self._item_data['baseType']

    @property
    def rarity(self) -> Rarity:
        rarity_str = self._item_data['rarity'].lower()
        return Rarity(rarity_str)

    @property
    def ilvl(self) -> int:
        return int(self._item_data['ilvl'])

    @property
    def level_requirement(self) -> int:
        reqs = self._item_data['requirements']
        return int(reqs[0]['values'][0][0]) if reqs and reqs[0]['name'] == 'Level' else 0

    @property
    def is_identified(self) -> bool:
        return 'identified' in self._item_data and self._item_data['identified'] is True

    @property
    def is_corrupted(self) -> bool:
        return 'corrupted' in self._item_data and self._item_data['corrupted'] is True

    @property
    def base_category(self) -> str:
        return shared_utils.extract_from_brackets(self._item_properties[0]['name'])

    def _extract_attribute_requirement(self, attribute_name: str):
        requirements = self._item_data['requirements']
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
