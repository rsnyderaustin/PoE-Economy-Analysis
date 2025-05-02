
from data_synthesizing.mods.mod import Mod
from .skill import Skill


class ItemListing:

    def __init__(self,
                 listing_id: str,
                 date_fetched: str,
                 price_currency: str,
                 price_amount: int,
                 item_name: str,
                 item_btype: str,  # Hunting Shoes, Lunar Amulet, etc
                 item_atype: str,  # DEX Body Armour, INT/DEX Gloves, One Handed Mace, etc
                 item_bgroup: str,  # Armour, Weapon, etc
                 rarity: str,
                 ilvl: int,
                 identified: bool,
                 corrupted: bool,
                 level_requirement: int,
                 str_requirement: int,
                 int_requirement: int,
                 dex_requirement: int,
                 implicit_mods: list[Mod],
                 enchant_mods: list[Mod],
                 rune_mods: list[Mod],
                 item_skills: list[Skill],
                 fractured_mods: list[Mod],
                 explicit_mods: list[Mod]
                 ):
        self.listing_id = listing_id
        self.date_fetched = date_fetched
        self.price_currency = price_currency
        self.price_amount = price_amount
        self.item_name = item_name
        self.item_btype = item_btype
        self.item_atype = item_atype
        self.item_bgroup = item_bgroup
        self.rarity = rarity
        self.ilvl = ilvl
        self.identified = identified
        self.corrupted = corrupted
        self.level_requirement = level_requirement
        self.str_requirement = str_requirement
        self.int_requirement = int_requirement
        self.dex_requirement = dex_requirement
        self.implicit_mods = implicit_mods
        self.enchant_mods = enchant_mods
        self.rune_mods = rune_mods
        self.item_skills = item_skills
        self.fractured_mods = fractured_mods
        self.explicit_mods = explicit_mods

    @property
    def mods(self) -> list[Mod]:
        all_mods = (
                self.implicit_mods +
                self.enchant_mods +
                self.rune_mods +
                self.fractured_mods +
                self.explicit_mods
        )
        return all_mods
