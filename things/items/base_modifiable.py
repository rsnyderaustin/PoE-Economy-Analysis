
from utils.enums import ModifierClass, ModAffixType
from .base_item import Item
from .mod import Mod


class Modifiable(Item):

    def __init__(self,
                 item_id: str,
                 name: str,
                 btype_name: str,
                 quality: int,
                 corrupted: bool,
                 ilvl: int,
                 implicit_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None,
                 enchant_mods: list[Mod] = None,
                 rune_mods: list[Mod] = None,
                 fractured_mods: list[Mod] = None
                 ):
        super(Item).__init__(
            item_id=item_id,
            name=name,
            btype_name=btype_name,
            corrupted=corrupted,
            quality=quality
        )
        self.ilvl = ilvl

        self.implicit_mods = implicit_mods or []
        self.explicit_mods = explicit_mods or []
        self.enchant_mods = enchant_mods or []
        self.rune_mods = rune_mods or []
        self.fractured_mods = fractured_mods or []

    @property
    def prefixes(self):
        return [mod for mod in getattr(self, ModifierClass.EXPLICIT.value)
                if mod.mod_type_enum == ModAffixType.PREFIX]

    @property
    def suffixes(self):
        return [mod for mod in getattr(self, ModifierClass.EXPLICIT.value)
                if mod.mod_type_enum == ModAffixType.SUFFIX.value]






