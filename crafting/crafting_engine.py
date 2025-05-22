from instances_and_definitions import ModifiableListing, ModAffixType, ItemMod, ModClass
from .crafting_outcome import CraftingOutcome
from .mods import ModsManager


class CraftingEngine:

    def __init__(self):
        # Need to validate that we have all or nearly all of the mods represented in Poecd
        self.mods_manager = ModsManager()

    def roll_new_modifier(self,
                          listing: ModifiableListing,
                          affix_types: list[ModAffixType],
                          force_type: str = None,
                          exclude_mod_ids: set = None) -> list[CraftingOutcome]:
        """

        :param listing:
        :param affix_types:
        :param force_type:
        :param exclude_mod_ids: If not supplied, the function assumes that all current mods on the item are not eligible to roll.
        :return: All the possible crafting outcomes given the function's parameters
        """

        atype_item_mods = self.mods_manager.fetch_mod_tiers(
            atype=listing.item_atype,
            max_ilvl=listing.ilvl,
            force_mod_type=force_type,
            exclude_mod_ids=set(mod.mod_id for mod in listing.mods) if not exclude_mod_ids else exclude_mod_ids,
            affix_types=affix_types
        )

        total_weight = sum(item_mod.weighting for item_mod in atype_item_mods)

        outcomes = [
            CraftingOutcome(
                original_listing=listing,
                outcome_probability=item_mod.weighting / total_weight,
                new_item_mod=item_mod
            )
            for item_mod in atype_item_mods
        ]

        return outcomes

    @staticmethod
    def create_crafting_outcomes(listing: ModifiableListing,
                                 item_mods: list[ItemMod],
                                 exclude_mod_ids: list[int] = None) -> list[CraftingOutcome]:
        valid_item_mods = [item_mod for item_mod in item_mods if item_mod.mod_id not in exclude_mod_ids]

        total_mod_weight = sum(item_mod.weighting for item_mod in item_mods)

        crafting_outcomes = []
        for item_mod in valid_item_mods:
            crafting_outcome = CraftingOutcome(
                original_listing=listing,
                outcome_probability=item_mod.weighting / total_mod_weight,
                new_item_mod=item_mod
            )
            crafting_outcomes.append(crafting_outcome)

        return crafting_outcomes

    @staticmethod
    def apply_crafting_outcome(listing: ModifiableListing,
                               outcome: CraftingOutcome) -> ModifiableListing:
        mod_class_to_attribute = {
            ModClass.IMPLICIT: listing.implicit_mods,
            ModClass.ENCHANT: listing.enchant_mods,
            ModClass.FRACTURED: listing.fractured_mods,
            ModClass.EXPLICIT: listing.explicit_mods
        }
        if outcome.new_item_mod:
            new_mod = outcome.new_item_mod
            mod_attribute = mod_class_to_attribute[new_mod.mod_class_e]
            mod_attribute.append(new_mod)

        if outcome.remove_modifier:
            remove_mod = outcome.remove_modifier
            mod_attribute = mod_class_to_attribute[remove_mod.mod_class_e]
            mod_class_to_attribute[remove_mod.mod_class_e] = [mod for mod in mod_attribute
                                                              if mod.mod_id != remove_mod.mod_id]

        if outcome.new_rarity:
            listing.rarity = outcome.new_rarity

        if outcome.mods_fractured:
            for fractured_mod in outcome.mods_fractured:
                mod_attribute = mod_class_to_attribute[fractured_mod.mod_class_e]
                listing.fractured_mods.append(fractured_mod)
                mod_class_to_attribute[fractured_mod.mod_class_e] = [mod for mod in mod_attribute
                                                                     if mod.mod_id != fractured_mod.mod_id]

        if outcome.new_quality:
            listing.set_quality(outcome.new_quality)

        if outcome.new_sockets:
            listing.open_sockets += outcome.new_sockets

        return listing


