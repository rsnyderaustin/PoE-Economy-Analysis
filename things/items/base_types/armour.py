from things.items import Mod, Modifiable, Skill
from utils.enums import Rarity


class Armour(Modifiable):

    def __init__(self,
                 item_id: str,
                 name: str,
                 btype_name: str,
                 ilvl: int,
                 quality: int,
                 rarity: Rarity,
                 corrupted: bool,
                 sockets: list,
                 implicit_mods: list[str] = None,
                 enchant_mods: list[str] = None,
                 rune_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None,
                 granted_skills: list[Skill] = None
                 ):
        super(Modifiable).__init__(item_id=item_id,
                                   name=name,
                                   btype_name=btype_name,
                                   quality=quality,
                                   implicit_mods=implicit_mods,
                                   explicit_mods=explicit_mods,
                                   enchant_mods=enchant_mods,
                                   rune_mods=rune_mods)

        self.ilvl = ilvl
        self.rarity = rarity
        self.corrupted = corrupted
