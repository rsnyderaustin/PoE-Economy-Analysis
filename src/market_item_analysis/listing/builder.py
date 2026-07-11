import uuid
from datetime import datetime

import numpy as np

from src.market_item_analysis.trade_api.trade_result import ApiResponse
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Currency, Rarity
from src.market_item_analysis.listing.objects import EquipmentRequirements, ItemTypes, ListingMetadata, ItemMods, \
    EquipmentPrice, EquipmentProperties, EquipmentStats, ItemMod, EquipmentListing, EquipmentSkills, EquipmentCategories


class _EquipmentCategorizer:
    _wand_btype_map = {
        'volatile_wand': 'fire_wand',
        'withered_wand': 'chaos_wand',
        'bone_wand': 'physical_wand',
        'frigid_wand': 'cold_wand',
        'galvanic_wand': 'lightning_wand',
    }

    @classmethod
    def categorize(cls,
                   base_category: str,
                   base_name: str,
                   strength_requirement: int,
                   intelligence_requirement: int,
                   dexterity_requirement: int):
        if base_name in cls._wand_btype_map:
            return cls._wand_btype_map[base_name]

        _requirements_map = [
            ((strength_requirement, dexterity_requirement, intelligence_requirement), "(str/dex/int)"),
            ((strength_requirement, intelligence_requirement), "(str/int)"),
            ((strength_requirement, dexterity_requirement), "(str/dex)"),
            ((dexterity_requirement, intelligence_requirement), "(dex/int)"),
            ((strength_requirement,), "str"),
            ((dexterity_requirement,), "dex"),
            ((intelligence_requirement,), "int"),
        ]

        possible_categories = [base_category]

        possible_categories.extend([f"{base_category}_{suffix}" for reqs, suffix in _requirements_map if all(reqs)])

        for category in possible_categories:
            try:
                return EquipmentCategory(category)
            except ValueError:
                pass

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> "EquipmentCategory":
        return _EquipmentCategorizer.categorize(base_category=r.base_category,
                                                base_name=r.base_name,
                                                strength_requirement=r.strength_requirement,
                                                dexterity_requirement=r.dexterity_requirement,
                                                intelligence_requirement=r.intelligence_requirement)

class _ModFactory:

    _mod_abbrev_d = {
        ModClass.IMPLICIT: 'implicit',
        ModClass.ENCHANT: 'enchant',
        ModClass.EXPLICIT: 'explicit',
        ModClass.FRACTURED: 'fractured',
        ModClass.RUNE: 'rune'
    }

    @classmethod
    def create_mods(cls, r: ApiResponse) -> list[ItemMod]:
        all_mods = []
        for mod_class, mod_abbrev in cls._mod_abbrev_d.items():
            d_key = f"{mod_abbrev}Mods"
            if d_key not in r.item_data:
                continue

            mod_texts = r.item_data[d_key]
            new_mods = [ItemMod(mod_text=mod_text,
                                mod_class=mod_class) for mod_text in mod_texts]
            all_mods.extend(new_mods)

        return all_mods


class ListingBuilder:

    @classmethod
    def _mods_from_api_response(cls, r: ApiResponse) -> list[ItemMod]:
        all_mods = []
        for mod_class, mod_abbrev in cls._MOD_KEY_MAP.items():
            d_key = f"{mod_abbrev}Mods"
            if d_key not in r.item_data:
                continue

            mod_texts = r.item_data[d_key]
            new_mods = [ItemMod(mod_text=mod_text,
                                mod_class=mod_class) for mod_text in mod_texts]
            all_mods.extend(new_mods)

        return all_mods

    @classmethod
    def from_api_response(cls, r: ApiResponse) -> EquipmentListing:
        item_mods = ItemMods.from_api_response(r)
        price = EquipmentPrice.from_api_response(r)
        metadata = ListingMetadata.from_api_response(r)
        item_requirements = EquipmentRequirements.from_api_response(r)
        item_skills = EquipmentSkills.from_api_response(r)
        item_category = _EquipmentCategorizer.from_api_response(r)
        item_stats = EquipmentStats.from_api_response(r)

        item_types = ItemTypes(
            base_name=r.base_name,
            item_category=item_category
        )

        mod_informations = [
            m
            for mod_abbrev, mod_list in r.item_data['extended']['mods'].items()
            for m in mod_list
        ]
        suffixes = [m for m in mod_informations if m['tier'].startswith('S')]
        prefixes = [m for m in mod_informations if m['tier'].startswith('P')]
        item_properties = EquipmentProperties(
            rarity=Rarity(r.rarity),
            ilvl=r.ilvl,
            identified=r.is_identified,
            corrupted=r.is_corrupted,
            quality=r.quality
        )

        listing = EquipmentListing(
            internal_id=f"LST_{uuid.uuid4().hex[:10].upper()}",
            metadata=metadata,
            item_name=r.item_name,
            types=item_types,
            requirements=item_requirements,
            mods=item_mods,
            price=item_price,
            skills=item_skills,
            properties=item_properties,
            stats=item_stats
        )

        return listing
