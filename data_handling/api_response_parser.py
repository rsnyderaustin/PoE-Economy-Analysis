from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from shared import shared_utils
from shared.enums.item_enums import AType
from shared.enums.trade_enums import ModClass, Currency, Rarity
from shared.logging import LogsHandler, LogFile

parse_log = LogsHandler().fetch_log(LogFile.API_PARSING)


@dataclass
class Price:
    currency: Currency
    amount: int


class _ATypeClassifier:
    _wand_btype_map = {
        'volatile_wand': 'fire_wand',
        'withered_wand': 'chaos_wand',
        'bone_wand': 'physical_wand',
        'frigid_wand': 'cold_wand',
        'galvanic_wand': 'lightning_wand',
    }

    @classmethod
    def classify(cls, item_category: str, item_btype: str, str_req: int, int_req: int, dex_req: int):
        if item_btype in cls._wand_btype_map:
            return cls._wand_btype_map[item_btype]

        possible_atypes = [item_category]

        if str_req and int_req and dex_req:
            possible_atypes.append(f"{item_category}_(str/dex/int)")

        if str_req and int_req:
            possible_atypes.append(f"{item_category}_(str/int)")

        if str_req and dex_req:
            possible_atypes.append(f"{item_category}_(str/dex)")

        if dex_req and int_req:
            possible_atypes.append(f"{item_category}_(dex/int)")

        if str_req:
            possible_atypes.append(f"{item_category}_str")

        if dex_req:
            possible_atypes.append(f"{item_category}_dex")

        if int_req:
            possible_atypes.append(f"{item_category}_int")

        for atype in possible_atypes:
            try:
                return AType(atype)
            except ValueError:
                pass


class ApiResponseParser:
    _mod_class_to_abbrev = {
        ModClass.IMPLICIT: 'implicit',
        ModClass.ENCHANT: 'enchant',
        ModClass.EXPLICIT: 'explicit',
        ModClass.FRACTURED: 'fractured',
        ModClass.RUNE: 'rune'
    }

    _elemental_id_map = {
        4: 'fire_damage',
        5: 'cold_damage',
        6: 'lightning_damage'
    }

    def __init__(self, api_response_data: dict):
        self.api_d = self._clean_blank_spear_implicit(api_response_data)

        self.sub_mod_hash_to_text = self._determine_sub_mod_hash_to_text()
        self._properties = self._parse_properties()

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

    def _parse_properties(self) -> dict:
        properties = dict()

        if 'properties' not in self.item_data:
            parse_log.info(f"No item properties found for item '{self.item_name}'.")
            return dict()

        # The first property is the item category
        raw_properties = self.item_data['properties'][1:]

        for raw_property in raw_properties:
            property_name = raw_property['name']

            if property_name == 'elemental_damage':
                # Elemental damage is a hybrid of the different elemental damage types
                for ele_value in raw_property['values']:
                    elemental_type = self.__class__._elemental_id_map[ele_value[1]]
                    value = shared_utils.extract_average_from_text(ele_value[0])

                    properties[elemental_type] = value

                continue

            property_value_str = raw_property['values'][0][0]
            value = shared_utils.extract_average_from_text(property_value_str)

            properties[property_name] = value

        return properties

    def _determine_sub_mod_hash_to_text(self) -> dict:
        mod_classes = [e for e in ModClass if e != ModClass.RUNE]

        # ModClass: {sub_mod_hash: mod_text}
        hash_to_text = dict()
        for mod_class in mod_classes:
            abbrev_class = self.__class__._mod_class_to_abbrev[mod_class]

            if abbrev_class not in self.item_data['extended']['hashes']:
                continue

            hashes_list = self.item_data['extended']['hashes'][abbrev_class]

            hash_display_order = [mod_hash[0] for mod_hash in hashes_list]
            mod_text_display_order = self.item_data[mod_class.value]

            mod_id_to_text = {
                mod_id: mod_text
                for mod_id, mod_text in zip(hash_display_order, mod_text_display_order)
            }
            hash_to_text[mod_class] = mod_id_to_text

        return hash_to_text

    def fetch_sub_mod_hash_to_text(self, mod_class: ModClass) -> dict:
        return self.sub_mod_hash_to_text[mod_class] if mod_class in self.sub_mod_hash_to_text else dict()

    @property
    def item_data(self) -> dict:
        return self.api_d['item']

    @property
    def listing_data(self) -> dict:
        return self.api_d['listing']

    @property
    def skills_data(self) -> dict:
        return self.item_data['grantedSkills'] if 'grantedSkills' in self.item_data else dict()

    @property
    def date_fetched(self) -> datetime:
        formatted_date = self.listing_data['indexed'].lower().replace("z", "+00:00")
        return datetime.fromisoformat(formatted_date)

    @property
    def listing_id(self) -> str:
        return self.api_d['id']

    @property
    def mod_classes(self) -> list[ModClass]:
        # We aren't messing with runes right now
        return [mod_class for mod_class in ModClass
                if mod_class.value in self.item_data and mod_class != ModClass.RUNE]

    def fetch_mods_data(self, mod_class: ModClass) -> dict:
        abbrev_class = self.__class__._mod_class_to_abbrev[mod_class]
        mods_data = self.item_data['extended']['mods']
        return mods_data[abbrev_class] if abbrev_class in mods_data else dict()

    @property
    def account_name(self) -> str:
        return self.listing_data['account']['name']

    @property
    def price(self) -> Price:
        return Price(
            currency=Currency(self.listing_data['price']['currency']),
            amount=self.listing_data['price']['amount']
        )

    @property
    def item_name(self) -> str:
        return self.item_data['name']

    @property
    def item_btype(self) -> str:
        return self.item_data['baseType']

    @property
    def item_rarity(self) -> Rarity:
        rarity_str = self.item_data['rarity'].lower()
        return Rarity(rarity_str)

    @property
    def item_ilvl(self) -> int:
        return int(self.item_data['ilvl'])

    @property
    def is_identified(self) -> bool:
        return 'identified' in self.item_data and self.item_data['identified'] is True

    @property
    def is_corrupted(self) -> bool:
        return 'corrupted' in self.item_data and self.item_data['corrupted'] is True

    @property
    def item_atype(self) -> AType:
        item_category = self.item_data['properties'][0]['name']
        return _ATypeClassifier.classify(item_category=item_category,
                                         item_btype=self.item_btype,
                                         str_req=self.str_requirement,
                                         dex_req=self.dex_requirement,
                                         int_req=self.int_requirement)

    @property
    def item_properties(self) -> dict:
        return self._properties

    @property
    def str_requirement(self) -> int:
        requirements = self.item_data['requirements']
        str_req = [req for req in requirements if req['name'] == 'str']

        return int(str_req[0]['values'][0][0]) if str_req else 0

    @property
    def int_requirement(self) -> int:
        requirements = self.item_data['requirements']
        int_req = [req for req in requirements if req['name'] == 'int']
        return int(int_req[0]['values'][0][0]) if int_req else 0

    @property
    def dex_requirement(self) -> int:
        requirements = self.item_data['requirements']
        dex_req = [req for req in requirements if req['name'] == 'dex']
        return int(dex_req[0]['values'][0][0]) if dex_req else 0
