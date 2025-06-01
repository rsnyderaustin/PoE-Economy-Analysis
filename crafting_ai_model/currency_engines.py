import pprint
import random
from abc import abstractmethod, ABC

from crafting_ai_model.mod_rolling import ModRoller
from instances_and_definitions import ModifiableListing
from shared import ATypeGroups
from shared.enums.item_enums import AType
from shared.enums.trade_enums import Rarity, ModClass, Currency
from shared.logging import LogsHandler, LogFile, log_errors
from . import utils

craft_log = LogsHandler().fetch_log(LogFile.CRAFTING_MODEL)


class Outcome:

    def __init__(self, new_listing: ModifiableListing = None, listing_changed: bool = False):
        self.new_listing = new_listing
        self.listing_changed = listing_changed


class CurrencyEngine(ABC):
    currency_class = None

    @log_errors(craft_log)
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'currency_class') or cls.currency_class is None:
            raise ValueError(f"Class {cls.__name__} must define 'currency_class'")

    @abstractmethod
    def apply(self, mod_roller: ModRoller, listing: ModifiableListing) -> Outcome:
        pass


class ArcanistsEtcher(CurrencyEngine):
    currency_class = Currency.ARCANISTS_ETCHER

    @classmethod
    @log_errors(craft_log)
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ATypeGroups.fetch_non_martial_weapon_categories():
            craft_log.info(f"Arcanists Etcher: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Arcanists Etcher: Corrupted item is invalid")
            return Outcome()

        if listing.quality == listing.maximum_quality:
            craft_log.info(f"Arcanists Etcher: Item already at maximum quality ({listing.quality})")
            return Outcome()

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            raise ValueError(f"Arcanists Etcher: Invalid item rarity {listing.rarity}. See item data below:"
                             f"\n{pprint.pformat(listing.__dict__)}")

        new_quality = min(listing.maximum_quality, listing.quality + quality_increase)
        craft_log.info(f"Arcanists Etcher: Item with rarity {listing.rarity} had quality increased from "
                       f"{listing.quality} to {new_quality}")

        return Outcome(new_listing=listing)


class ArmourersScrap(CurrencyEngine):
    currency_class = Currency.ARMOURERS_SCRAP

    @log_errors(craft_log)
    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ATypeGroups.fetch_armour_categories():
            craft_log.info(f"Armourers Scrap: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Armourers Scrap: Corrupted item is invalid")
            return Outcome()

        if listing.quality == listing.maximum_quality:
            craft_log.info(f"Armourers Scrap: Item already at maximum quality ({listing.quality})")
            return Outcome()

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            raise ValueError(f"Invalid item rarity {listing.rarity}. See item data below:"
                             f"\n{pprint.pformat(listing.__dict__)}")

        new_quality = min(listing.maximum_quality, listing.quality + quality_increase)
        craft_log.info(f"Armourers Scrap: Item quality increased from {listing.quality} to {new_quality}")
        listing.set_quality(new_quality)

        return Outcome(new_listing=listing)


class ArtificersOrb(CurrencyEngine):
    currency_class = Currency.ARTIFICERS_ORB

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ATypeGroups.fetch_socketable_item_categories():
            return Outcome()

        if listing.corrupted:
            return Outcome()

        max_sockets = utils.determine_max_sockets(item_category=listing.item_category)

        total_listing_sockets = len(listing.socketers) + listing.open_sockets

        if total_listing_sockets == max_sockets:
            return Outcome()

        listing.open_sockets += 1
        return Outcome(new_listing=listing)


class BlacksmithsWhetstone(CurrencyEngine):
    currency_class = Currency.BLACKSMITHS_WHETSTONE

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ATypeGroups.fetch_martial_weapon_categories():
            craft_log.info(f"Blacksmiths Whetstone: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info(f"Blacksmiths Whetstone: Corrupted item is invalid")
            return Outcome()

        if listing.quality == listing.maximum_quality:
            craft_log.info(f"Blacksmiths Whetstone: Item already at maximum quality ({listing.quality})")
            return Outcome()

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            craft_log.info(f"{cls.__name__} not applicable to item with rarity {listing.rarity}.")
            return Outcome()

        new_quality = min(listing.maximum_quality, listing.quality + quality_increase)
        craft_log.info(f"Blacksmiths Whetstone: Item quality increased from {listing.quality} to {new_quality}")
        listing.set_quality(new_quality)

        return Outcome(new_listing=listing)


class ChaosOrb(CurrencyEngine):
    currency_class = Currency.CHAOS_ORB

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM, AType.LIFE_FLASK, AType.MANA_FLASK):
            craft_log.info(f"Chaos Orb: Item category {listing.item_category} invalid.")
            return Outcome()

        if listing.rarity != Rarity.RARE:
            craft_log.info(f"Chaos Orb: Item rarity {listing.rarity} invalid.")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Chaos Orb: Corrupted item is invalid.")
            return Outcome()

        removed_mod = listing.removable_mods[random.randint(0, len(listing.removable_mods))]
        craft_log.info(f"Chaos Orb: Removed existing mod {removed_mod.mod_id}")

        # Remove the mod
        mods_of_removed_mod_class = listing.fetch_mods(removed_mod.mod_class)
        for i, mod in enumerate(mods_of_removed_mod_class):
            if mod == removed_mod:
                del mods_of_removed_mod_class[i]
                break

        new_mod = mod_roller.roll_new_modifier(listing=listing,
                                               mod_class=ModClass.EXPLICIT)
        craft_log.info(f"Chaos Orb: Rolled new mod {new_mod.mod_id}")
        listing.fetch_mods(new_mod.mod_class).append(new_mod)

        return Outcome(new_listing=listing)


class DivineOrb(CurrencyEngine):
    currency_class = Currency.DIVINE_ORB

    @classmethod
    @log_errors(craft_log)
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM, AType.LIFE_FLASK, AType.MANA_FLASK):
            craft_log.info(f"Divine Orb: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.rarity == Rarity.NORMAL:
            craft_log.info(f"Divine Orb: Invalid rarity {listing.rarity}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Divine Orb: Corrupted item is invalid.")
            return Outcome()

        mods_to_reroll = [*listing.implicit_mods, *listing.enchant_mods, *listing.explicit_mods]
        sub_mods_to_reroll = [sub_mod for mod in mods_to_reroll for sub_mod in mod.sub_mods]
        values_log = {sub_mod.values_ranges: sub_mod.actual_values for sub_mod in sub_mods_to_reroll}
        craft_log.info(f"Divine Orb:\nOld mod values and ranges:\n{pprint.pformat(values_log)}")

        for sub_mod in sub_mods_to_reroll:
            if not sub_mod.values_ranges:
                continue

            new_actual_values = []
            for actual_value, value_range in zip(sub_mod.actual_values, sub_mod.values_ranges):
                low_r = value_range[0]
                high_r = value_range[1]
                if low_r is None or high_r is None:
                    value = low_r if high_r is None else high_r
                    new_actual_values.append(value)
                    continue

                if low_r is not None and high_r is not None:
                    if isinstance(low_r, int) and isinstance(high_r, int):
                        new_value = random.randint(low_r, high_r)
                        new_actual_values.append(new_value)
                    elif isinstance(low_r, float) and isinstance(high_r, float):
                        new_value = round(random.uniform(low_r, high_r), 2)
                        new_actual_values.append(new_value)
                    else:  # This should only happen when there is no range
                        raise ValueError(f"Received unexpected value types for range {low_r} - {high_r}")

            sub_mod.actual_values = new_actual_values

        values_log = {sub_mod.values_ranges: sub_mod.actual_values for sub_mod in sub_mods_to_reroll}
        craft_log.info(f"Divine Orb:\nNew mod values and ranges:\n{pprint.pformat(values_log)}")

        return Outcome(new_listing=listing)


class ExaltedOrb(CurrencyEngine):
    currency_class = Currency.EXALTED_ORB

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM, AType.LIFE_FLASK, AType.MANA_FLASK):
            craft_log.info(f"Exalted Orb: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.rarity != Rarity.RARE:
            craft_log.info(f"Exalted Orb: Invalid rarity {listing.rarity}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Exalted Orb: Corrupted item is invalid.")
            return Outcome()

        if not listing.open_prefixes and not listing.open_suffixes:
            craft_log.info("Exalted Orb: Invalid due to no open prefixes or suffixes")
            return Outcome()

        new_mod = mod_roller.roll_new_modifier(listing=listing,
                                               mod_class=ModClass.EXPLICIT)
        craft_log.info(f"Exalted Orb: Item rolled new mod {new_mod.mod_id}")
        listing.fetch_mods(new_mod.mod_class).append(new_mod)

        return Outcome(new_listing=listing)


class FracturingOrb(CurrencyEngine):
    currency_class = Currency.FRACTURING_ORB

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM, AType.LIFE_FLASK, AType.MANA_FLASK):
            craft_log.info(f"Fracturing Orb: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info(f"Fracturing Orb: Corrupted item is invalid")
            return Outcome()

        if listing.rarity != Rarity.RARE:
            craft_log.info(f"Fracturing Orb: Invalid item rarity {listing.rarity}")
            return Outcome()

        if listing.fractured_mods:  # You cannot fracture mods on an item that already has fractured mods
            craft_log.info(f"Fracturing Orb: Item is invalid due to presence of existing fractured mods.")
            return Outcome()

        fractured_mod = listing.removable_mods[random.randint(0, len(listing.removable_mods))]
        craft_log.info(f"Fracturing Orb: Fractured existing mod {fractured_mod.mod_id}")

        # Fracture a mod, removing it from its current mod class list and adding it to the fractured mods
        mods_of_fractured_mod_class = listing.fetch_mods(fractured_mod.mod_class)
        for i, mod in enumerate(mods_of_fractured_mod_class):
            if mod == fractured_mod:
                del mods_of_fractured_mod_class[i]
                listing.fractured_mods.append(mod)


class GemcuttersPrism(CurrencyEngine):
    currency_class = Currency.GEMCUTTERS_PRISM

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in [AType.SKILL_GEM, AType.META_GEM]:
            craft_log.info(f"Gemcutters Prism: Item category {listing.item_category} is invalid.")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Gemcutters Prism: Corrupted item is invalid.")
            return Outcome()

        if listing.quality == listing.maximum_quality:
            craft_log.info(f"Gemcutters Prism: Item is invalid. Already at maximum quality ({listing.quality}")
            return Outcome()

        new_quality = min(listing.quality + 5, listing.maximum_quality)
        craft_log.info(f"Gemcutters Prism: Item quality increased from {listing.quality} to {new_quality}")
        listing.set_quality(new_quality)

        return Outcome(new_listing=listing)


class GlassblowersBauble(CurrencyEngine):
    currency_class = Currency.GLASSBLOWERS_BAUBLE

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ATypeGroups.fetch_flask_categories():
            craft_log.info(f"Glassblowers Bauble: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info(f"Glassblowers Bauble: Corrupted item is invalid.")
            return Outcome()

        if listing.quality == listing.maximum_quality:
            craft_log.info(f"Glassblowers Bauble: Item is invalid. Already at maximum quality ({listing.quality})")
            return Outcome()

        new_quality = listing.quality + 1
        craft_log.info(f"Glassblowers Bauble: Quality increased from {listing.quality} to {new_quality}")
        listing.set_quality(new_quality)

        return Outcome(new_listing=listing)


class OrbOfAlchemy(CurrencyEngine):
    currency_class = Currency.ORB_OF_ALCHEMY

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.LIFE_FLASK, AType.MANA_FLASK, AType.META_GEM, AType.SKILL_GEM):
            craft_log.info(f"Orb of Alchemy: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.rarity != Rarity.NORMAL:
            craft_log.info(f"Orb of Alchemy: Invalid item rarity {listing.rarity}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Orb of Alchemy: Corrupted item is invalid")
            return Outcome()

        listing.rarity = Rarity.RARE

        num_mods = random.randint(3, 4) if listing.item_category == AType.JEWEL else random.randint(4, 6)

        for _ in list(range(num_mods)):
            new_mod = mod_roller.roll_new_modifier(listing=listing,
                                                   mod_class=ModClass.EXPLICIT)
            listing.fetch_mods(new_mod.mod_class).append(new_mod)

        craft_log.info(f"Orb of Alchemy: {listing.item_category} item rolled {num_mods} new mods:\n"
                       f"{listing.fetch_mods(ModClass.EXPLICIT)}")

        return Outcome(new_listing=listing)


class OrbOfAnnulment(CurrencyEngine):
    currency_class = Currency.ORB_OF_ANNULMENT

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM):
            craft_log.info(f"Orb of Annulment: Invalid item category {listing.item_category}")
            return Outcome()

        if not listing.explicit_mods:
            craft_log.info("Orb of Annulment: Item has no explicit mods. Invalid.")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Orb of Annulment: Corrupted item is invalid.")
            return Outcome()

        if listing.rarity not in (Rarity.MAGIC, Rarity.RARE):
            craft_log.info(f"Orb of Annulment: Item rarity {listing.rarity} is invalid.")
            return Outcome()

        removed_mod = listing.removable_mods[random.randint(0, len(listing.removable_mods))]
        craft_log.info(f"Orb of Annulment: Removed mod {removed_mod.mod_id}.")

        # Remove the mod
        mods_of_removed_mod_class = listing.fetch_mods(removed_mod.mod_class)
        for i, mod in enumerate(mods_of_removed_mod_class):
            if mod == removed_mod:
                del mods_of_removed_mod_class[i]
                break

        return Outcome(new_listing=listing)


class OrbOfAugmentation(CurrencyEngine):
    currency_class = Currency.ORB_OF_AUGMENTATION

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM):
            craft_log.info(f"Orb of Augmentation: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Orb of Augmentation: Corrupted item is invalid.")
            return Outcome()

        if listing.rarity != Rarity.MAGIC:
            craft_log.info(f"Orb of Augmentation: Invalid item rarity {listing.rarity}")
            return Outcome()

        if not listing.open_prefixes and not listing.open_suffixes:
            craft_log.info("Orb of Augmentation: Item has no open prefixes or suffixes. Invalid.")
            return Outcome()

        new_mod = mod_roller.roll_new_modifier(listing=listing,
                                               mod_class=ModClass.EXPLICIT)
        craft_log.info(f"Orb of Augmentation: Rolled new mod {new_mod.mod_id}")
        listing.fetch_mods(new_mod.mod_class).append(new_mod)

        return Outcome(new_listing=listing)


class OrbOfTransmutation(CurrencyEngine):
    currency_class = Currency.TRANSMUTATION_SHARD

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM):
            craft_log.info(f"Orb of Transmutation: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Orb of Transmutation: Corrupted item is invalid")
            return Outcome()

        if listing.rarity != Rarity.NORMAL:
            craft_log.info(f"Orb of Transmutation: Invalid item rarity {listing.rarity}")
            return Outcome()

        listing.rarity = Rarity.MAGIC

        num_mods = random.randint(1, 2)

        log_new_mods = []
        for _ in list(range(num_mods)):
            new_mod = mod_roller.roll_new_modifier(listing=listing,
                                                   mod_class=ModClass.EXPLICIT)
            listing.explicit_mods.append(new_mod)
            log_new_mods.append(new_mod)

        craft_log.info(f"Orb of Transmutation: Item rolled {num_mods} new mods. New mods:\n{log_new_mods}")

        return Outcome(new_listing=listing)


class RegalOrb(CurrencyEngine):
    currency_class = Currency.REGAL_ORB

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (AType.SKILL_GEM, AType.META_GEM, AType.LIFE_FLASK, AType.MANA_FLASK):
            return Outcome()

        if listing.rarity != Rarity.MAGIC:
            return Outcome()

        if listing.corrupted:
            return Outcome()

        listing.rarity = Rarity.RARE

        new_mod = mod_roller.roll_new_modifier(listing=listing,
                                               mod_class=ModClass.EXPLICIT)
        listing.explicit_mods.append(new_mod)

        return Outcome(new_listing=listing)


class ScrollOfWisdom(CurrencyEngine):
    currency_class = Currency.SCROLL_OF_WISDOM

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        # You technically can identify corrupted items, but we don't currently have the proper data to roll enchanted mods
        if listing.corrupted:
            craft_log.info("Scroll of Wisdom: Corrupted item not currently supported.")
            return Outcome()

        if listing.identified:
            craft_log.info("Scroll of Wisdom: Item is already identified. Invalid.")
            return Outcome()

        listing.identified = True

        if listing.rarity == Rarity.MAGIC:
            num_mods = random.randint(1, 2)
        elif listing.rarity == Rarity.RARE:
            num_mods = random.randint(4, 6)
        else:
            num_mods = 0

        log_new_mods = []
        for _ in list(range(num_mods)):
            new_mod = mod_roller.roll_new_modifier(listing=listing,
                                                   mod_class=ModClass.EXPLICIT)
            listing.explicit_mods.append(new_mod)
            log_new_mods.append(new_mod)

        craft_log.info(f"Scroll of Wisdom: Item rolled {num_mods} new mods. New mods:\n{log_new_mods}")

        return Outcome(new_listing=listing)
