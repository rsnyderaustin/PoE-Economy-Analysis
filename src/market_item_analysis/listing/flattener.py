import logging
from enum import Enum

from src.market_item_analysis.instances_and_definitions.item_instances import EquipmentListing
from src.market_item_analysis.shared.enums import EquipmentCategoryGroups, WhichCategoryType
from src.market_item_analysis.shared.enums.item_enums import CalculatedMod
from src.market_item_analysis.shared.text_analysis import TextAnalyzer

logger = logging.getLogger(__name__)


class CalculatedMod(Enum):
    MAX_QUALITY_PDPS = 'max_quality_pdps'
    FIRE_DPS = 'fire_dps'
    COLD_DPS = 'cold_dps'
    LIGHTNING_DPS = 'lightning_dps'
    ELEMENTAL_DPS = 'elemental_dps'
    CHAOS_DPS = 'chaos_dps'

    MAX_QUALITY_ARMOUR = 'max_quality_armour'
    MAX_QUALITY_ENERGY_SHIELD = 'max_quality_energy_shield'
    MAX_QUALITY_EVASION = 'max_quality_evasion'


class ListingFlattener:

    @classmethod
    def flatten_listing(cls, listing: EquipmentListing) -> dict:
        d = dict()
        is_martial_weapon = listing.types.item_category in EquipmentCategoryGroups.fetch_martial_weapon_categories(which=WhichCategoryType.Equipment)
        if is_martial_weapon:
            d.update(cls._calculate_non_physical_dps(listing=listing))
            d.update(cls._calculate_max_physical_dps(listing=listing))

        is_armour = listing.types.item_category in EquipmentCategoryGroups.fetch_armour_categories(which=WhichCategoryType.Equipment)
        if is_armour:
            d.update(cls._calculate_max_armour_stats(listing=listing))

        flattened_d = cls._flatten_listing(listing=listing,
                                           include_stats=not is_martial_weapon and not is_armour)
        d.update(flattened_d)

        return d

    @classmethod
    def _calculate_max_armour_stats(cls, listing: EquipmentListing) -> dict:
        current_multiplier = 1 + (listing.properties.quality / 100)

        max_quality = 20
        max_multiplier = 1 + (max_quality / 100)

        # Calculate the base damage and then the 20% quality damage
        base_armour = listing.stats.armour / current_multiplier
        max_quality_armour = base_armour * max_multiplier

        base_energy_shield = listing.stats.energy_shield / current_multiplier
        max_quality_energy_shield = base_energy_shield * max_multiplier

        base_evasion = listing.stats.evasion / current_multiplier
        max_quality_evasion = base_evasion * max_multiplier

        return {
            CalculatedMod.MAX_QUALITY_ARMOUR: max_quality_armour,
            CalculatedMod.MAX_QUALITY_ENERGY_SHIELD: max_quality_energy_shield,
            CalculatedMod.MAX_QUALITY_EVASION: max_quality_evasion
        }

    @classmethod
    def _calculate_non_physical_dps(cls, listing: EquipmentListing) -> dict:
        attacks_per_second = listing.stats.attacks_per_second or 0
        cold_dps = listing.stats.cold_damage * attacks_per_second
        fire_dps = listing.stats.fire_damage * attacks_per_second
        lightning_dps = listing.stats.lightning_damage * attacks_per_second
        chaos_dps = listing.stats.chaos_damage * attacks_per_second
        elemental_dps = (
                (listing.stats.cold_damage + listing.stats.fire_damage + listing.stats.lightning_damage)
                * attacks_per_second
        )
        return {
            CalculatedMod.COLD_DPS: cold_dps,
            CalculatedMod.FIRE_DPS: fire_dps,
            CalculatedMod.LIGHTNING_DPS: lightning_dps,
            CalculatedMod.CHAOS_DPS: chaos_dps,
            CalculatedMod.ELEMENTAL_DPS: elemental_dps,
        }

    @classmethod
    def _calculate_max_physical_dps(cls, listing: EquipmentListing) -> dict:
        current_multiplier = 1 + (listing.properties.quality / 100)

        max_quality = 20
        max_multiplier = 1 + (max_quality / 100)

        # Calculate the base damage and then the 20% quality damage
        base_damage = listing.stats.physical_damage / current_multiplier
        max_quality_damage = base_damage * max_multiplier

        max_quality_pdps = (listing.stats.attacks_per_second or 0) * max_quality_damage

        return {CalculatedMod.MAX_QUALITY_PDPS: max_quality_pdps}

    @classmethod
    def _flatten_listing(cls,
                         listing: EquipmentListing,
                         include_stats: bool) -> dict:
        d = dict()
        d.update(listing.metadata.to_dict())
        d.update(listing.price.to_dict())
        d['item_name'] = listing.item_name
        d.update(listing.types.to_dict())
        d.update(listing.requirements.to_dict())
        if include_stats:
            d.update(listing.stats.to_dict())

        for mod in listing.mods_.all_mods:
            mod_values, sanitized_mod_text = TextAnalyzer.extract_numbers_from_string(mod.mod_text)
            for i, mod_value in enumerate(mod_values):
                d[f"{mod}_{i}_sanitized_mod_text"] = mod_value

        d.update({skill.name: skill.level for skill in listing.skills})
        d.update(listing.properties.to_dict())

        return d

