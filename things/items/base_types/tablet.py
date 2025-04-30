from things.items import Mod, Modifiable
from utils import Rarity


class Jewellery(Modifiable):

    def __init__(self,
                 item_id: str,
                 name: str,
                 btype_name: str,
                 ilvl: int,
                 quality: int,
                 rarity: Rarity,
                 corrupted: bool,
                 explicit_mods: list[Mod] = None,
                 implicit_mods: list[str] = None
                 ):
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   btype_name=btype_name,
                                   quality=quality,
                                   implicit_mods=implicit_mods,
                                   explicit_mods=explicit_mods)

        self.ilvl = ilvl
        self.rarity = rarity
        self.corrupted = corrupted

