
from abc import ABC

from item.attributes.mod import Mod
from api_mediation import AttributeFactory


class Item(ABC):

    def __init__(self,
                 item_id: str,
                 name: str,
                 base_type: str
                 ):
        self.item_id = item_id
        self.name = name
        self.base_type = base_type

        self.enchant_mods = [
            AttributeFactory.create_mod(enchant_mod)
            for enchant_mod in enchant_mods
        ] if enchant_mods else []

        self.rune_mods = [
            AttributeFactory.create_mod(rune_mod)
            for rune_mod in rune_mods
        ] if rune_mods else []

        self.explicit_mods = [
            AttributeFactory.create_mod(explicit_mod)
            for explicit_mod in explicit_mods
        ] if explicit_mods else []

        self.fractured_mods = [
            AttributeFactory.create_mod(fractured_mod)
            for fractured_mod in fractured_mods
        ] if fractured_mods else []

        self.granted_skills = [
            AttributeFactory.create_skill(granted_skill)
            for granted_skill in granted_skills
        ] if granted_skills else []

