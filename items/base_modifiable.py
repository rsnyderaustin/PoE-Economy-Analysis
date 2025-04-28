
from abc import ABC

from items import Item, Mod
from utils import ItemAttributes


class Modifiable(ABC, Item):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 quality: int,
                 implicit_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None,
                 enchant_mods: list[Mod] = None,
                 rune_mods: list[Mod] = None
                 ):
        super(Item).__init__(
            item_id=item_id,
            name=name,
            base_type=base_type
        )
        setattr(self, ItemAttributes.MiscAttribute.QUALITY.value, quality)

        setattr(self, ItemAttributes.Modifier.IMPLICIT.value, implicit_mods or [])
        setattr(self, ItemAttributes.Modifier.EXPLICIT.value, explicit_mods or [])
        setattr(self, ItemAttributes.Modifier.ENCHANT.value, enchant_mods or [])
        setattr(self, ItemAttributes.Modifier.RUNE.value, rune_mods or [])
        setattr(self, ItemAttributes.Modifier.FRACTURED.value, fractured_mods or [])

    @property
    def modifiers(self) -> list[Mod]:
        mod_lists = [
            getattr(self, mod_type.value) for mod_type in ItemAttributes.Modifier
        ]
        mods = [mod for mod_list in mod_lists for mod in mod_list]
        return mods

    @property
    def prefixes(self):
        return [mod for mod in self.]






