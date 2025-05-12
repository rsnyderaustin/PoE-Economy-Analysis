import logging
from abc import abstractmethod, ABC

from crafting import CraftingOutcome
from crafting.crafting_engine import CraftingEngine
from instances_and_definitions import ModifiableListing, ModAffixType
from shared.trade_item_enums import Rarity, ItemCategory


class CurrencyEngine(ABC):
    item_id = None

    @abstractmethod
    def apply(self, crafting_engine: CraftingEngine, listing: ModifiableListing):
        pass

    @staticmethod
    def no_outcome_change(listing: ModifiableListing) -> CraftingOutcome:
        return CraftingOutcome(
            original_listing=listing,
            outcome_probability=1.0
        )


class ArcanistsEtcher(CurrencyEngine):
    item_id = 'etcher'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.item_category not in classifications.non_martial_weapons:
            return [cls.no_outcome_change(listing=listing)]

        item_quality = listing.quality if listing.quality else 0

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            logging.info(f"{cls.__name__} not applicable to item with rarity {listing.rarity}.")
            return [cls.no_outcome_change(listing=listing)]

        if item_quality == listing.maximum_quality:
            return [cls.no_outcome_change(listing=listing)]

        return [
            CraftingOutcome(
                original_listing=listing,
                outcome_probability=1.0,
                new_quality=min(listing.maximum_quality, item_quality + quality_increase)
            )
        ]


class ArmourersScrap(CurrencyEngine):
    item_id = 'scrap'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.item_category not in classifications.armour:
            return [cls.no_outcome_change(listing=listing)]

        item_quality = listing.quality if listing.quality else 0

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            logging.info(f"{cls.__name__} not applicable to item with rarity {listing.rarity}.")
            return [cls.no_outcome_change(listing=listing)]

        if item_quality == listing.maximum_quality:
            return [cls.no_outcome_change(listing=listing)]

        return [
            CraftingOutcome(
                original_listing=listing,
                outcome_probability=1.0,
                new_quality=min(listing.maximum_quality, item_quality + quality_increase)
            )
        ]


class ArtificersOrb(CurrencyEngine):
    item_id = 'artificers'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        max_atype_sockets = helper_funcs.determine_max_sockets(atype=listing.atype)

        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if max_atype_sockets == 0:
            return [cls.no_outcome_change(listing=listing)]

        item_sockets = 0 if not listing.num_sockets else listing.num_sockets

        if item_sockets < max_atype_sockets:
            return [
                CraftingOutcome(
                    original_listing=listing,
                    outcome_probability=1.0,
                    new_sockets=1
                )
            ]


class BlacksmithsWhetstone(CurrencyEngine):
    item_id = 'whetstone'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.item_category not in classifications.martial_weapons:
            return [cls.no_outcome_change(listing=listing)]

        item_quality = listing.quality if listing.quality else 0

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            logging.info(f"{cls.__name__} not applicable to item with rarity {listing.rarity}.")
            return [cls.no_outcome_change(listing=listing)]

        if item_quality == listing.maximum_quality:
            return [cls.no_outcome_change(listing=listing)]

        return [
            CraftingOutcome(
                original_listing=listing,
                outcome_probability=1.0,
                new_quality=min(listing.maximum_quality, item_quality + quality_increase)
            )
        ]


class ChaosOrb(CurrencyEngine):
    item_id = 'chaos'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.rarity != Rarity.RARE:
            return [
                cls.no_outcome_change(listing=listing)
            ]

        if listing.corrupted:
            return [
                cls.no_outcome_change(listing=listing)
            ]

        open_prefixes = 3 - len(listing.prefixes)

        open_suffixes = 3 - len(listing.suffixes)

        irremovable_mod_ids = set(
            irremovable_mod.mod_id for irremovable_mod in listing.permanent_mods
        )

        returnable_outcomes = []
        # If there are open prefixes, then we can roll any prefix no matter what is removed. The same is true for suffixes.
        # Note that when rolling for a new modifier, chaos orbs can replace the same mod they just removed with the same mod.
        # So we pass only the modifiers that cannot be removed (fractured mods) to exclude_mod_ids parameter
        possible_crafting_outcomes = crafting_engine.roll_new_modifier(listing=listing,
                                                                       affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX],
                                                                       exclude_mod_ids=irremovable_mod_ids)
        for modifier in listing.explicit_mods:
            if open_prefixes and open_suffixes:
                viable_mod_tiers = possible_crafting_outcomes
            # If we rolled a prefix and there are no open suffixes then we CANNOT roll a suffix
            elif modifier.affix_type == ModAffixType.PREFIX and not open_suffixes:
                viable_mod_tiers = [mod for mod in possible_crafting_outcomes if mod.affix_type == ModAffixType.PREFIX]
            # If we rolled a suffix and there are no open prefixes then we CANNOT roll a prefix
            elif modifier.affix_type == ModAffixType.SUFFIX and not open_prefixes:
                viable_mod_tiers = [mod for mod in possible_crafting_outcomes if mod.affix_type == ModAffixType.SUFFIX]
            # In all other cases, we can roll any mod
            else:
                viable_mod_tiers = possible_crafting_outcomes

            other_mod_ids = [listing_mod.mod_id for listing_mod in listing.affixed_mods if listing_mod != modifier]
            crafting_outcomes = crafting_engine.roll_new_modifier(
                listing=listing,
                mod_tiers=viable_mod_tiers,
                exclude_mod_ids=other_mod_ids,
            )

            for outcome in crafting_outcomes:
                outcome.remove_modifier = modifier
                outcome.outcome_probability /= len(listing.explicit_mods)

            returnable_outcomes.extend(crafting_outcomes)

        return returnable_outcomes


class ExaltedOrb(CurrencyEngine):
    item_id = 'exalt'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.rarity != Rarity.RARE:
            return [
                cls.no_outcome_change(listing=listing)
            ]

        if listing.corrupted:
            return [
                cls.no_outcome_change(listing=listing)
            ]

        open_prefixes = 3 - len(listing.prefixes)
        open_suffixes = 3 - len(listing.suffixes)

        if not open_prefixes and not open_suffixes:
            return [
                cls.no_outcome_change(listing=listing)
            ]

        affix_types = []
        if open_prefixes:
            affix_types.append(ModAffixType.PREFIX)

        if open_suffixes:
            affix_types.append(ModAffixType.SUFFIX)

        possible_mod_tiers = crafting_engine.roll_new_modifier(listing=listing,
                                                               affix_types=affix_types)
        crafting_outcomes = crafting_engine.roll_new_modifier(listing=listing,
                                                              mod_tiers=possible_mod_tiers)
        return crafting_outcomes


class FracturingOrb(CurrencyEngine):
    item_id = 'fracturing-orb'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.fractured_mods:
            return [cls.no_outcome_change(listing=listing)]

        outcomes = []
        for mod in listing.explicit_mods:
            outcomes.append(
                CraftingOutcome(
                    original_listing=listing,
                    outcome_probability=(1.0 / len(listing.explicit_mods)),
                    mods_fractured=[mod]
                )
            )

        return outcomes


class GemcuttersPrism(CurrencyEngine):
    item_id = 'gcp'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.item_category != ItemCategory.ANY_GEM:
            return [cls.no_outcome_change(listing=listing)]

        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        new_quality = listing.quality + 5
        new_quality = min(new_quality, listing.maximum_quality)

        return [
            CraftingOutcome(
                original_listing=listing,
                outcome_probability=1.0,
                new_quality=new_quality
            )
        ]


class GlassblowersBauble(CurrencyEngine):
    item_id = 'bauble'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.item_category != ItemCategory.ANY_FLASK:
            return [cls.no_outcome_change(listing=listing)]

        item_quality = listing.quality if listing.quality else 0

        return [
            CraftingOutcome(
                original_listing=listing,
                outcome_probability=1.0,
                new_quality=min(listing.maximum_quality, item_quality + 1)
            )
        ]


class OrbOfAlchemy(CurrencyEngine):
    item_id = 'alch'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.rarity != Rarity.NORMAL:
            return [cls.no_outcome_change(listing=listing)]

        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        possible_mod_tiers = crafting_engine.roll_new_modifier(listing=listing,
                                                               affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX])
        crafting_outcomes = crafting_engine.roll_new_modifier(listing=listing,
                                                              mod_tiers=possible_mod_tiers)
        for outcome in crafting_outcomes:
            outcome.new_rarity = Rarity.RARE

        return crafting_outcomes


class OrbOfAnnulment(CurrencyEngine):
    item_id = 'annul'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if not listing.explicit_mods:
            return [cls.no_outcome_change(listing=listing)]

        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        outcomes = []
        for mod in listing.removable_mods:
            outcomes.append(
                CraftingOutcome(
                    original_listing=listing,
                    outcome_probability=(1 / len(listing.removable_mods)),
                    remove_modifier=mod
                )
            )

        return outcomes


class OrbOfAugmentation(CurrencyEngine):
    item_id = 'aug'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.rarity != Rarity.MAGIC:
            return [cls.no_outcome_change(listing=listing)]

        open_prefixes = 1 - len(listing.prefixes)
        open_suffixes = 1 - len(listing.suffixes)

        if not open_prefixes and not open_suffixes:
            return [cls.no_outcome_change(listing=listing)]

        affix_types = []
        if open_prefixes:
            affix_types.append(ModAffixType.PREFIX)

        if open_suffixes:
            affix_types.append(ModAffixType.SUFFIX)


class OrbOfTransmutation(CurrencyEngine):
    item_id = 'transmute'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        if listing.rarity != Rarity.NORMAL:
            return [cls.no_outcome_change(listing=listing)]

        outcomes = crafting_engine.roll_new_modifier(listing=listing,
                                                     affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX])
        for outcome in outcomes:
            outcome.new_rarity = Rarity.MAGIC

        return outcomes


class RegalOrb(CurrencyEngine):
    item_id = 'regal'

    @classmethod
    def apply(cls, crafting_engine: CraftingEngine, listing: ModifiableListing) -> list[CraftingOutcome]:
        if listing.rarity != Rarity.MAGIC:
            return [cls.no_outcome_change(listing=listing)]

        if listing.corrupted:
            return [cls.no_outcome_change(listing=listing)]

        possible_mod_tiers = crafting_engine.roll_new_modifier(listing=listing,
                                                               affix_types=[ModAffixType.SUFFIX, ModAffixType.PREFIX])
        crafting_outcomes = crafting_engine.roll_new_modifier(listing=listing,
                                                              mod_tiers=possible_mod_tiers)
        for outcome in crafting_outcomes:
            outcome.new_rarity = Rarity.RARE

        return crafting_outcomes
