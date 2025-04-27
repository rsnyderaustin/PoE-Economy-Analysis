from .price import Price
from utils import Currency, RawToEnum
from .price import Price


class ApiInterfacer:


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

            item_json = object_json['items']
            new_item = cls._create_item(item_json=item_json)

            

