
from things.items import Item, Mod
from utils.enums import ItemAttributes, ModAffixType


class Modifiable(Item):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str,
                 quality: int,
                 implicit_mods: list[Mod] = None,
                 explicit_mods: list[Mod] = None,
                 enchant_mods: list[Mod] = None,
                 rune_mods: list[Mod] = None,
                 fractured_mods: list[Mod] = None
                 ):
        super(Item).__init__(
            item_id=item_id,
            name=name,
            base_type=base_type
        )
        self.quality = quality

        self.implicit_mods = implicit_mods or []
        self.explicit_mods = explicit_mods or []
        self.enchant_mods = enchant_mods or []
        self.rune_mods = rune_mods or []
        self.fractured_mods = fractured_mods or []

    @property
    def modifiers(self) -> list[Mod]:
        mod_lists = [
            getattr(self, mod_type.value) for mod_type in ItemAttributes.Modifier
        ]
        mods = [mod for mod_list in mod_lists for mod in mod_list]
        return mods

    @property
    def prefixes(self):
        return [mod for mod in getattr(self, ItemAttributes.Modifier.EXPLICIT.value)
                if mod.mod_type_enum == ModAffixType.PREFIX]

    @property
    def suffixes(self):
        return [mod for mod in getattr(self, ItemAttributes.Modifier.EXPLICIT.value)
                if mod.mod_type_enum == ModAffixType.SUFFIX.value]






