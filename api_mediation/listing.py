
from api_mediation.price import Price
from item import Item


class Listing:

    def __init__(self,
                 listed_by: str,
                 item: Item,
                 listing_id: str,
                 price: Price):
        self.listed_by = listed_by
        self.item = item
        self.listing_id = listing_id
        self.price = price


