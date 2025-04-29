
from things.items import Item


class Gem(Item):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type_name: str,
                 quality: int,
                 corrupted: bool):
        super(Item).__init__(item_id=item_id,
                             name=name,
                             base_type_name=base_type_name,
                             corrupted=corrupted)

        self.quality = quality

