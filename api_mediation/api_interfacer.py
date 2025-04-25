
from .attribute_factory import AttributeFactory
from .price import Price
from item import Item
from utils import Currency, Rarity, RawToEnum


class ApiInterfacer:

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


    @classmethod
    def parse_listing(cls, trade_json):
        object_jsons = trade_json['result']

        for object_json in object_jsons:
            listing_id = object_json['id']

            price_json = object_json['listing']['price']
            price = Price(
                currency=RawToEnum(enum_class=Currency,
                                   enum_value=price_json['currency']
                                   ),
                amount=price_json['amount']
            )

            item_json = object_json['item']
            new_item = cls._create_item(item_json=item_json)

            

