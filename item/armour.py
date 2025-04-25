
from .item import Item
from api_mediation import Mod
from utils import Rarity


class Socketable(Item):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 ilvl: int,
                 quality: int,
                 rarity: Rarity,
                 corrupted: bool,
                 enchant_mods: list[str] = None,
                 rune_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None,
                 fractured_mods: list[Mod] = None,
                 granted_skills: list[Mod] = None):
        super().__init__(item_id=item_id,
                         name=name,
                         base_type=base_type)

        self.ilvl = ilvl
        self.quality = quality
        self.rarity = rarity
        self.corrupted = corrupted

        self.enchant_mods = enchant_mods or []
        self.rune_mods = rune_mods or []
        self.explicit_mods = explicit_mods or []
        self.fractured_mods = fractured_mods or []
        self.granted_skills = granted_skills or []

