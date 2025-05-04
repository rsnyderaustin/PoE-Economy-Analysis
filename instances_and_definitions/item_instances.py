from shared.enums import ModClass, ModAffixType


class ItemAffixedMod:

    def __init__(self,
                 mod_class: ModClass,
                 mod_affix_type: ModAffixType,
                 mod_texts: list[str],
                 mod_values: list):
        """
        As of right now this only applies to Explicit mods and Fractured mods.
        """
        self.mod_class = mod_class
        self.mod_affix_type = mod_affix_type
        self.mod_texts = mod_texts
        self.mod_values = mod_values


class ItemNonAffixedMod:

    def __init__(self,
                 mod_class: ModClass,
                 mod_text: str,
                 mod_values: list):
        """
        As of right now this only applies to Enchant mods and Implicit mods.
        """
        self.mod_class = mod_class
        self.mod_text = mod_text
        self.mod_values = mod_values


class ItemSkill:

    def __init__(self,
                 name: str,
                 level: int):
        self.name = name
        self.level = level


class ItemSocketer:

    def __init__(self, name: str, text: str):
        """
        Socketers have no rolls and thus do not differ from item to item. Their text is static.
        """
        self.name = name
        self.text = text
