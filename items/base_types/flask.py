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
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   base_type=base_type,
                                   quality=quality,
                                   explicit_mods=explicit_mods)

        self.ilvl = ilvl
        self.rarity = rarity
        self.corrupted = corrupted

