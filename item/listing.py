
from .price import Price
from api_mediation.attribute_factory import AttributeFactory
from item import Item


class Listing:

    def __init__(self,
                 item: Item,
                 listing_id: str,
                 price: Price):
        self.item = item
        self.listing_id = listing_id
        self.price = price


