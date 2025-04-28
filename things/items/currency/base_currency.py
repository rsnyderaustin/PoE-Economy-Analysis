
from abc import ABC, abstractmethod

from things.items import Item


class Currency(ABC):

    def __init__(self,
                 item_id: str,
                 readable_name: str):
        self.item_id = item_id
        self.readable_name = readable_name

    @abstractmethod
    def modify_item(self, item: Item):
        pass
