
from items import Mod, Modifiable
from utils import ItemAttributes, Rarity


class Weapon(Modifiable):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 ilvl: int,
                 quality: int,
                 rarity: Rarity,
                 corrupted: bool,
                 sockets: list,
                 implicit_mods: list[str] = None,
                 enchant_mods: list[str] = None,
                 rune_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None,
                 fractured_mods: list[Mod] = None,
                 granted_skills: list[Mod] = None):
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   base_type=base_type,
                                   quality=quality,
                                   implicit_mods=implicit_mods,
                                   explicit_mods=explicit_mods,
                                   enchant_mods=enchant_mods,
                                   rune_mods=rune_mods,
                                   fractured_mods=fractured_mods)

        setattr(self, ItemAttributes.MiscAttribute.RARITY.value, rarity)
        setattr(self, ItemAttributes.MiscAttribute.ILVL.value, ilvl)
        setattr(self, ItemAttributes.MiscAttribute.CORRUPTED.value, corrupted)



