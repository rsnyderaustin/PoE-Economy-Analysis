import pprint
import random
from abc import abstractmethod, ABC

from crafting_ai_model.mod_rolling import ModRoller
from instances_and_definitions import ModifiableListing
from shared import ItemCategoryGroups, LogsHandler, LogFile
from shared.enums.item_enums import ItemCategory
from shared.enums.trade_enums import Rarity, ModClass
from . import utils


craft_log = LogsHandler().fetch_log(LogFile.CRAFTING_MODEL)


class Outcome:

    def __init__(self, new_listing: ModifiableListing = None, listing_changed: bool = False):
        self.new_listing = new_listing
        self.listing_changed = listing_changed


class CurrencyEngine(ABC):
    item_id = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'item_id') or cls.item_id is None:
            raise ValueError(f"Class {cls.__name__} must define 'item_id'")

    @abstractmethod
    def apply(self, mod_roller: ModRoller, listing: ModifiableListing) -> Outcome:
        pass

    def __str__(self):
        return self.__class__.item_id


class ArcanistsEtcher(CurrencyEngine):
    item_id = 'etcher'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ItemCategoryGroups.fetch_non_martial_weapon_categories():
            return Outcome()

        if listing.corrupted:
            return Outcome()

        item_quality = listing.quality if listing.quality else 0

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            return Outcome()

        if item_quality == listing.maximum_quality:
            return Outcome()

        listing.quality = min(listing.maximum_quality, item_quality + quality_increase)
        return Outcome(new_listing=listing)


class ArmourersScrap(CurrencyEngine):
    item_id = 'scrap'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ItemCategoryGroups.fetch_armour_categories():
            return Outcome()

        if listing.corrupted:
            return Outcome()

        item_quality = listing.quality if listing.quality else 0

        if listing.rarity == Rarity.NORMAL:
            quality_increase = 5
        elif listing.rarity == Rarity.MAGIC:
            quality_increase = 2
        elif listing.rarity in (Rarity.RARE, Rarity.UNIQUE):
            quality_increase = 1
        else:
            return Outcome()

        if item_quality == listing.maximum_quality:
            return Outcome()

        listing.quality = min(listing.maximum_quality, item_quality + quality_increase)
        return Outcome(new_listing=listing)


class ArtificersOrb(CurrencyEngine):

    item_id = 'artificers'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ItemCategoryGroups.fetch_socketable_item_categories():
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
    item_id = 'whetstone'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ItemCategoryGroups.fetch_martial_weapon_categories():
            return Outcome()

        if listing.corrupted:
            return Outcome()

        item_quality = listing.quality if listing.quality else 0
        if item_quality == listing.maximum_quality:
            craft_log.info(f"Blacksmiths Whetstone: Item at max quality ({item_quality})")
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

        listing.quality = min(listing.maximum_quality, item_quality + quality_increase)
        craft_log.info(f"Blacksmiths Whetstone: Item quality {item_quality} -> {listing.quality}")
        return Outcome(new_listing=listing)


class ChaosOrb(CurrencyEngine):
    item_id = 'chaos'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM, ItemCategory.LIFE_FLASK, ItemCategory.MANA_FLASK):
            craft_log.info(f"Chaos Orb: Item category {listing.item_category} invalid.")
            return Outcome()

        if listing.rarity != Rarity.RARE:
            craft_log.info(f"Chaos Orb: Item rarity {listing.rarity} invalid.")
            return Outcome()

        if listing.corrupted:
            craft_log.info("Chaos Orb: Corrupted item is invalid.")
            return Outcome()

        removed_mod = listing.removable_mods[random.randint(0, len(listing.removable_mods))]
        craft_log.info(f"Chaos Orb: Removed existing mod {pprint.pprint(removed_mod)}")

        # Remove the mod
        mods_of_removed_mod_class = listing.fetch_mods(removed_mod.mod_class_e)
        for i, mod in enumerate(mods_of_removed_mod_class):
            if mod == removed_mod:
                del mods_of_removed_mod_class[i]
                break

        new_mod = mod_roller.roll_new_modifier(listing=listing,
                                               mod_class=ModClass.EXPLICIT)
        craft_log.info(f"Chaos Orb: Rolled new mod {pprint.pprint(new_mod)}")
        listing.fetch_mods(new_mod.mod_class_e).append(new_mod)

        return Outcome(new_listing=listing)


class DivineOrb(CurrencyEngine):
    item_id = 'divine'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM, ItemCategory.LIFE_FLASK, ItemCategory.MANA_FLASK):
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
        craft_log.info(f"Divine Orb:\nOld mod values {pprint.pprint(values_log)}")
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
        craft_log.info(f"Divine Orb:\nNew mod values {pprint.pprint(values_log)}")

        return Outcome(new_listing=listing)


class ExaltedOrb(CurrencyEngine):
    item_id = 'exalt'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM, ItemCategory.LIFE_FLASK, ItemCategory.MANA_FLASK):
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
        craft_log.info(f"Exalted Orb: Item rolled new mod {pprint.pprint(new_mod)}")
        listing.fetch_mods(new_mod.mod_class_e).append(new_mod)

        return Outcome(new_listing=listing)


class FracturingOrb(CurrencyEngine):
    item_id = 'fracturing-orb'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM, ItemCategory.LIFE_FLASK, ItemCategory.MANA_FLASK):
            craft_log.info(f"Fracturing Orb: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info(f"Fracturing Orb: Corrupted item is invalid")
            return Outcome()

        if listing.rarity != Rarity.RARE:
            craft_log.info(f"Fracturing Orb: Invalid item rarity {listing.item_rarity}")
            return Outcome()

        if listing.fractured_mods:  # You cannot fracture mods on an item that already has fractured mods
            craft_log.info(f"Fracturing Orb: Item is invalid due to presence of existing fractured mods.")
            return Outcome()

        fractured_mod = listing.removable_mods[random.randint(0, len(listing.removable_mods))]

        # Fracture a mod, removing it from its current mod class list and adding it to the fractured mods
        mods_of_fractured_mod_class = listing.fetch_mods(fractured_mod.mod_class_e)
        for i, mod in enumerate(mods_of_fractured_mod_class):
            if mod == fractured_mod:
                del mods_of_fractured_mod_class[i]
                listing.fractured_mods.append(mod)


class GemcuttersPrism(CurrencyEngine):
    item_id = 'gcp'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in [ItemCategory.SKILL_GEM, ItemCategory.META_GEM]:
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
        listing.quality = new_quality

        return Outcome(new_listing=listing)


class GlassblowersBauble(CurrencyEngine):
    item_id = 'bauble'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category not in ItemCategoryGroups.fetch_flask_categories():
            craft_log.info(f"Glassblowers Bauble: Invalid item category {listing.item_category}")
            return Outcome()

        if listing.corrupted:
            craft_log.info(f"Glassblowers Bauble: Corrupted item is invalid.")
            return Outcome()

        if listing.quality == listing.maximum_quality:
            craft_log.info(f"Glassblowers Bauble: Item is invalid. Already at maximum quality ({listing.quality})")
            return Outcome()

        listing.quality += 1
        craft_log.info(f"Glassblowers Bauble: Quality increased from {listing.quality - 1} to {listing.quality}")

        return Outcome(new_listing=listing)


class OrbOfAlchemy(CurrencyEngine):
    item_id = 'alch'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.LIFE_FLASK, ItemCategory.MANA_FLASK, ItemCategory.META_GEM, ItemCategory.SKILL_GEM):
            return Outcome()

        if listing.rarity != Rarity.NORMAL:
            return Outcome()

        if listing.corrupted:
            return Outcome()

        listing.rarity = Rarity.RARE

        num_mods = random.randint(4, 6)

        for _ in list(range(num_mods)):
            new_mod = mod_roller.roll_new_modifier(listing=listing,
                                                   mod_class=ModClass.EXPLICIT)
            listing.fetch_mods(new_mod.mod_class_e).append(new_mod)

        return Outcome(new_listing=listing)


class OrbOfAnnulment(CurrencyEngine):
    item_id = 'annul'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM):
            return Outcome()

        if not listing.explicit_mods:
            return Outcome()

        if listing.corrupted:
            return Outcome()

        if listing.rarity not in (Rarity.MAGIC, Rarity.RARE):
            return Outcome()

        removed_mod = listing.removable_mods[random.randint(0, len(listing.removable_mods))]

        # Remove the mod
        mods_of_removed_mod_class = listing.fetch_mods(removed_mod.mod_class_e)
        for i, mod in enumerate(mods_of_removed_mod_class):
            if mod == removed_mod:
                del mods_of_removed_mod_class[i]
                break

        return Outcome(new_listing=listing)


class OrbOfAugmentation(CurrencyEngine):
    item_id = 'aug'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM):
            return Outcome()

        if listing.corrupted:
            return Outcome()

        if listing.rarity != Rarity.MAGIC:
            return Outcome()

        if not listing.open_prefixes and not listing.open_suffixes:
            return Outcome()

        new_mod = mod_roller.roll_new_modifier(listing=listing,
                                               mod_class=ModClass.EXPLICIT)
        listing.fetch_mods(new_mod.mod_class_e).append(new_mod)

        return Outcome(new_listing=listing)


class OrbOfTransmutation(CurrencyEngine):
    item_id = 'transmute'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM):
            return Outcome()

        if listing.corrupted:
            return Outcome()

        if listing.rarity != Rarity.NORMAL:
            return Outcome()

        listing.rarity = Rarity.MAGIC

        num_mods = random.randint(1, 2)

        for _ in list(range(num_mods)):
            new_mod = mod_roller.roll_new_modifier(listing=listing,
                                                   mod_class=ModClass.EXPLICIT)
            listing.explicit_mods.append(new_mod)

        return Outcome(new_listing=listing)


class RegalOrb(CurrencyEngine):
    item_id = 'regal'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        if listing.item_category in (ItemCategory.SKILL_GEM, ItemCategory.META_GEM, ItemCategory.LIFE_FLASK, ItemCategory.MANA_FLASK):
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
    item_id = 'wisdom'

    @classmethod
    def apply(cls, mod_roller: ModRoller, listing: ModifiableListing):
        # You technically can identify corrupted items, but we don't currently have the proper data to roll enchanted mods
        if listing.corrupted:
            return Outcome()

        if listing.identified:
            return Outcome()

        listing.identified = True

        if listing.rarity == Rarity.MAGIC:
            num_mods = random.randint(1, 2)
        elif listing.rarity == Rarity.RARE:
            num_mods = random.randint(4, 6)
        else:
            num_mods = 0

        for _ in list(range(num_mods)):
            new_mod = mod_roller.roll_new_modifier(listing=listing,
                                                   mod_class=ModClass.EXPLICIT)
            listing.explicit_mods.append(new_mod)

        return Outcome(new_listing=listing)
