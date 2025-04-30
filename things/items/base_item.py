
from abc import ABC


class Item(ABC):

    def __init__(self,
                 item_id: str,
                 name: str,
                 btype_name: str,
                 corrupted: bool,
                 quality: int
                 ):
        self.item_id = item_id
        self.name = name
        self.btype = btype_name
        self.corrupted = corrupted
        self.quality = quality

