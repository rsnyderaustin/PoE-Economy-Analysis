
from abc import ABC, abstractmethod

from things.items import Item


class CurrencyEngine(ABC):

    @abstractmethod
    def apply(self, item: Item):
        pass
