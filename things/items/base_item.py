
from abc import ABC


class Item(ABC):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type_name: str,
                 corrupted: bool,
                 quality: int
                 ):
        self.item_id = item_id
        self.name = name
        self.base_type = base_type_name
        self.corrupted = corrupted
        self.quality = quality

