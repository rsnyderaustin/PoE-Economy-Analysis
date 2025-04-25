
from abc import ABC, abstractmethod

from items.attributes.mod import Mod
from api_mediation import AttributeFactory
from utils import ItemType


class Item(ABC):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str
                 ):
        self.item_id = item_id
        self.name = name
        self.base_type = base_type

