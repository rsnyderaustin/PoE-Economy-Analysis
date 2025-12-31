import uuid
from datetime import datetime

import numpy as np

from src.market_item_analysis.instances_and_definitions import ItemMod, ItemSkill, EquipmentListing
from src.market_item_analysis.trade_api.api_response_obj import ApiResponse
from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Currency, Rarity
from ..instances_and_definitions.item_instances import EquipmentRequirements, ItemTypes, ListingMetadata, ItemMods, Price, EquipmentProperties, EquipmentStats
from ..shared.text_analysis import TextAnalyzer


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


class _StatsDiscoverer:

    @classmethod
    def _pull_value(cls, stat: str, r: ApiResponse) -> float | int | None:
        properties_list = r.item_data['properties']
        stat_dicts = [d for d in properties_list if d['name'] == stat]
        if not stat_dicts:
            return None

        if len(stat_dicts) >= 2:
            raise ValueError(f"Found 2 stats dicts for {stat}.\nSource data: {properties_list}")

        val_str = stat_dicts[0]['values'][0]
        vals = TextAnalyzer.extract_numbers_from_string(val_str)
        return np.mean(vals)

    @classmethod
    def determine_stats(cls, r: ApiResponse) -> EquipmentStats:
        armour = cls._pull_value(stat='[Armour]', r=r)
        evasion = cls._pull_value(stat='[Evasion|Evasion Rating]', r=r)
        energy_shield = cls._pull_value(stat='[Energy Shield|Energy Shield]', r=r)

        elemental_damage = r.determine_elemental_damage_values()

        phys_damage = cls._pull_value(stat='[Physical] Damage', r=r)
        crit_chance = cls._pull_value(stat='[Critical|Critical Hit] Chance', r=r)
        attacks_per_second = cls._pull_value(stat='Attacks per Second', r=r)

        return EquipmentStats(
            armour=armour,
            evasion=evasion,
            energy_shield=energy_shield,
            fire_damage=elemental_damage.fire,
            cold_damage=elemental_damage.cold,
            lightning_damage=elemental_damage.lightning,
            physical_damage=phys_damage,
            critical_hit_chance=crit_chance,
            attacks_per_second=attacks_per_second
        )


class _SkillsFactory:

    @staticmethod
    def create_skills(r: ApiResponse) -> list[ItemSkill]:
        if not r.skills_data:
            return []

        skills = []
        for skill_data in r.skills_data:
            raw_skill = skill_data['values'][0]

            # Spear Throw is the only skill that is granted by an item without a level. May have to update in the future
            if raw_skill[0] == 'Spear Throw':
                new_skill = ItemSkill(
                    name='Spear Throw'
                )
                skills.append(new_skill)
                continue

            if isinstance(raw_skill, str):
                _, level_str, *skill_parts = raw_skill.split()
                level = int(level_str)
                skill_name = ' '.join(skill_parts)
            else:
                skill_name = raw_skill[0][0]
                level = raw_skill[0][1]

            new_skill = ItemSkill(
                name=skill_name,
                level=level
            )

            skills.append(new_skill)

        return skills


class ListingBuilder:

    @classmethod
    def build_listing(cls, r: ApiResponse):
        item_mods_list = _ModFactory.create_mods(r)
        item_mods = ItemMods(
            implicits=[mod for mod in item_mods_list if mod.mod_class == ModClass.IMPLICIT],
            enchants=[mod for mod in item_mods_list if mod.mod_class == ModClass.ENCHANT],
            fractures=[mod for mod in item_mods_list if mod.mod_class == ModClass.FRACTURED],
            explicits=[mod for mod in item_mods_list if mod.mod_class == ModClass.EXPLICIT],
        )

        item_price = Price(
            currency=Currency(r.price_currency),
            currency_amount=r.price_amount,
            gold_cost=r.gold_cost
        )

        metadata = ListingMetadata(
            poster_account_name=r.account_name,
            listing_id=r.listing_id,
            date_posted=r.date_fetched,
            date_fetched=datetime.now()
        )

        item_requirements = EquipmentRequirements(
            player_level=r.level_requirement,
            strength=r.strength_requirement,
            intelligence=r.intelligence_requirement,
            dexterity=r.dexterity_requirement
        )

        item_skills = _SkillsFactory.create_skills(r)

        item_category = _EquipmentCategorizer.categorize(base_category=r.base_category,
                                                         base_name=r.base_name,
                                                         strength_requirement=r.strength_requirement,
                                                         dexterity_requirement=r.dexterity_requirement,
                                                         intelligence_requirement=r.intelligence_requirement)

        item_stats = _StatsDiscoverer.determine_stats(r)

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
            quality=r.quality,
            open_suffixes=max(len(suffixes) - 3, 0),
            open_prefixes=max(len(prefixes) - 3, 0),
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
