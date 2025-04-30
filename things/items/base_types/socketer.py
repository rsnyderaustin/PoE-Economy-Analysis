
from things.items.base_item import Item


class Socketer(Item):

    def __init__(self, item_id: str, name: str, btype_name: str):
        super().__init__(item_id=item_id,
                         name=name,
                         btype_name=btype_name)


