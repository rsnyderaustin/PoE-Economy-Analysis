from items import Item, Mod, Modifiable
from utils import ItemAttributes, Rarity


class Jewellery(Modifiable):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 ilvl: int,
                 quality: int,
                 rarity: Rarity,
                 corrupted: bool,
                 explicit_mods: list[Mod] = None,
                 implicit_mods: list[str] = None
                 ):
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   base_type=base_type,
                                   quality=quality,
                                   implicit_mods=implicit_mods,
                                   explicit_mods=explicit_mods)

        setattr(self, ItemAttributes.MiscAttribute.ILVL.value, ilvl)
        setattr(self, ItemAttributes.MiscAttribute.RARITY.value, rarity)
        setattr(self, ItemAttributes.MiscAttribute.CORRUPTED.value, corrupted)

