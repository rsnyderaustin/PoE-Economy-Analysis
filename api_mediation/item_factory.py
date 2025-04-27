
from utils import Rarity, RawToEnum
from .attribute_factory import AttributeFactory


def determine_item_class(item_type: str):
    


class ItemFactory:

    @classmethod
    def _create_mods(cls, item_json, mod_string):
        if mod_string in item_json:
            mods = [
                AttributeFactory.create_mod(
                    raw_string=mod_string
                ) for mod_string in item_json[mod_string]
            ]

        return mods


    @classmethod
    def _create_item(cls, item_json):
        item_id = item_json['id']
        item_type = item_json['properties'][0]['name']
        name = item_json['name']
        base_type = item_json['baseType']
        ilvl = item_json['ilvl']
        rarity = RawToEnum(enum_class=Rarity,
                           enum_value=item_json['rarity'])

        enchant_mods = cls._create_mods(
            item_json=item_json,
            mod_string='enchantMods'
        )

        rune_mods = cls._create_mods(
            item_json=item_json,
            mod_string='runeMods'
        )

        implicit_mods = cls._create_mods(
            item_json=item_json,
            mod_string='implicitMods'
        )

        explicit_mods = cls._create_mods(
            item_json=item_json,
            mod_string='explicitMods'
        )

        fractured_mods = cls._create_mods(
            item_json=item_json,
            mod_string='fracturedMods'
        )
