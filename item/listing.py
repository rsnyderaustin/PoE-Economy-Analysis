
from .price import Price
from .attribute_factory import AttributeFactory


class Listing:

    def __init__(self,
                 listing_id: str,
                 name: str,
                 ilvl: int,
                 price: Price,
                 enchant_mods: list[str] = None,
                 rune_mods: list[str] = None,
                 explicit_mods: list[str] = None,
                 fractured_mods: list[str] = None,
                 granted_skills: list[str] = None):
        self.listing_id = listing_id
        self.name = name
        self.ilvl = ilvl
        self.price = price

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

