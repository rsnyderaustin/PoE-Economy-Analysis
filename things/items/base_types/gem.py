
from things.items import Item


class Gem(Item):

    def __init__(self,
                 item_id: str,
                 name: str,
                 btype_name: str,
                 quality: int,
                 corrupted: bool):
        super(Item).__init__(item_id=item_id,
                             name=name,
                             btype_name=btype_name,
                             corrupted=corrupted)

        self.quality = quality

