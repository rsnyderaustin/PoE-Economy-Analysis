
from item import Price
from utils import currency_to_enum


class ApiInterfacer:

    @classmethod
    def parse_listing(cls, trade_json):
        object_jsons = trade_json['result']

        for object_json in object_jsons:
            listing_id = object_json['id']

            price_json = object_json['listing']['price']
            price = Price(
                currency=currency_to_enum[price_json['currency']],
                amount=price_json['amount']
            )

            item_json = object_json['item']

            

