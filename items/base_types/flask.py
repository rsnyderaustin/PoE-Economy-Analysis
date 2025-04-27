from items import Mod, Modifiable
from utils import ItemAttributes, Rarity


class Flask(Modifiable):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 ilvl: int,
                 quality: int,
                 rarity: Rarity,
                 corrupted: bool,
                 explicit_mods: list[Mod] = None
                 ):
        setattr(self, ItemAttributes.MiscAttribute.ILVL.value, ilvl)
        setattr(self, ItemAttributes.MiscAttribute.RARITY.value, rarity)
        setattr(self, ItemAttributes.MiscAttribute.CORRUPTED.value, corrupted)
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   base_type=base_type,
                                   quality=quality,
                                   explicit_mods=explicit_mods)

