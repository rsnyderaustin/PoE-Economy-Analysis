import logging
from dataclasses import dataclass

from .item_enums import ItemCategory
from .trade_enums import ModClass, Currency, Rarity
from . import shared_utils


@dataclass
class Price:
    currency: Currency
    amount: int


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

        self._mod_id_to_text = self._determine_mod_id_to_mod_text()
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
            logging.info(f"No item properties found for item '{self.item_name}'.")
            return dict()

        # The first property is the item category
        raw_properties = self.item_data['properties'][1:]

        for raw_property in raw_properties:
            property_name = raw_property['name']

            if property_name == 'elemental_damage':
                # Elemental damage is a hybrid of the different elemental damage types
                for ele_value in raw_property['values']:
                    value = shared_utils.extract_values_from_text(ele_value[0])
                    elemental_type = self.__class__._elemental_id_map[ele_value[1]]
                    properties[elemental_type] = value

                continue
            property_value_str = raw_property['values'][0][0]
            property_values = shared_utils.extract_values_from_text(property_value_str)
            properties[property_name] = property_values

        return properties

    def _determine_mod_id_to_mod_text(self) -> dict:
        mod_classes = [e for e in ModClass if e != ModClass.RUNE]

        # ModClass: {mod_id: mod_text}
        id_to_text_dict = dict()
        for mod_class_e in mod_classes:
            abbrev_class = self.__class__._mod_class_to_abbrev[mod_class_e]

            if abbrev_class not in self.item_data['extended']['hashes']:
                return dict()

            hashes_list = self.item_data['extended']['hashes'][abbrev_class]

            mod_id_display_order = [mod_hash[0] for mod_hash in hashes_list]
            mod_text_display_order = self.item_data[mod_class_e.value]

            mod_id_to_text = {
                mod_id: shared_utils.sanitize_mod_text(mod_text)
                for mod_id, mod_text in zip(mod_id_display_order, mod_text_display_order)
            }
            id_to_text_dict[mod_class_e] = mod_id_to_text

        return id_to_text_dict

    def fetch_mod_id_to_mod_text(self, mod_class: ModClass) -> dict:
        return self._mod_id_to_text[mod_class] if mod_class in self._mod_id_to_text else dict()

    @property
    def item_data(self):
        return self.api_d['item']

    @property
    def listing_data(self):
        return self.api_d['listing']

    @property
    def skills_data(self) -> dict:
        return self.item_data['grantedSkills'] if 'grantedSkills' in self.item_data else dict()

    @property
    def date_fetched(self):
        return self.listing_data['indexed']

    @property
    def listing_id(self):
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
    def account_name(self):
        return self.listing_data['account']['name']

    @property
    def price(self) -> Price:
        return Price(
            currency=self.listing_data['price']['currency'],
            amount=self.listing_data['price']['amount']
        )

    @property
    def item_name(self):
        return self.item_data['name']

    @property
    def item_btype(self):
        return self.item_data['baseType']

    @property
    def item_rarity(self) -> Rarity:
        rarity_str = self.item_data['rarity'].lower()
        return Rarity(rarity_str)

    @property
    def item_ilvl(self):
        return int(self.item_data['ilvl'])

    @property
    def is_identified(self) -> bool:
        return 'identified' in self.item_data

    @property
    def is_corrupted(self):
        return 'corrupted' in self.item_data

    @property
    def item_category(self) -> ItemCategory:
        category_str = self.item_data['properties'][0]['name']
        return ItemCategory(category_str)

    @property
    def item_properties(self) -> dict:
        return self._properties

    @property
    def str_requirement(self) -> int:
        requirements = self.item_data['requirements']
        str_req = [req for req in requirements if req.name == '[Strength|Str]']
        return int(str_req[0]['values']) if str_req else 0

    @property
    def int_requirement(self) -> int:
        requirements = self.item_data['requirements']
        int_req = [req for req in requirements if req.name == '[Intelligence|Int]']
        return int(int_req[0]['values']) if int_req else 0

    @property
    def dex_requirement(self) -> int:
        requirements = self.item_data['requirements']
        dex_req = [req for req in requirements if req.name == '[Dexterity|Dex]']
        return int(dex_req[0]['values']) if dex_req else 0
        


