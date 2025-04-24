
from .item import Item
from utils import JewelRadius


class Jewel(Item):

    def __init__(self, name: str, base_type: str, ilvl: int, corrupted: bool, radius: JewelRadius = None):
        super().__init__(name, base_type, ilvl, corrupted)

        self.radius = radius



