
from abc import ABC

from utils import ModClass, generate_mod_id


class ModTier:

    def __init__(self,
                 parent_mod_id: str,
                 affix_type: str,
                 atype: str,
                 sub_mod_id_to_values_ranges: dict[str: list],
                 ilvl_requirement: int,
                 weighting: float):
        self.parent_mod_id = parent_mod_id
        self.affix_type = affix_type
        self.atype = atype
        self.sub_mod_id_to_values_ranges = sub_mod_id_to_values_ranges
        self.ilvl_requirement = ilvl_requirement
        self.weighting = weighting


class ModDefinition(ABC):
    mod_classes = [e for e in ModClass]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'mod_classes'):
            raise NotImplementedError(f"{cls.__name__} must define a class variable 'mod_classes'")


class AffixedModDefinition:
    mod_classes = [ModClass.FRACTURED, ModClass.EXPLICIT]

    def __init__(self,
                 mod_class: ModClass,
                 atype: str,
                 mod_tiers: list[ModTier]):
        self.mod_class = mod_class
        self.atype = atype
        self.mod_tiers = mod_tiers


class NonAffixedModDefinition:
    mod_classes = [ModClass.RUNE, ModClass.ENCHANT]

    def __init__(self,
                 atype: str,
                 sanitized_mod_text: str,
                 mod_id: str = None):
        self.atype = atype
        self.sanitized_mod_text = sanitized_mod_text

        self.mod_id = generate_mod_id(atype=atype, mod_ids=[mod_id] if mod_id else [], mod_text=sanitized_mod_text)


class SkillDefinition:

    def __init__(self,
                 name: str,
                 levels_range: list[int]):
        self.name = name
        self.levels_range = levels_range


class SocketerDefinition:

    def __init__(self, name: str, text: str):
        """
        Socketers have no rolls and thus do not differ from item to item. Their text is static.
        """
        self.name = name
        self.text = text
