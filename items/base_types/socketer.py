
from items.base_item import Item


class Socketer(Item):

    def __init__(self, item_id: str, name: str, base_type: str):
        super().__init__(item_id=item_id,
                         name=name,
                         base_type=base_type)


