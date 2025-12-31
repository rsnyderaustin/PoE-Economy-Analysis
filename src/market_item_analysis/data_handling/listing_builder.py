import copy
import uuid
from datetime import datetime

from src.market_item_analysis.file_management.file_managers import ItemModsFile
from src.market_item_analysis.instances_and_definitions import ItemMod,  ItemSkill, EquipmentListing
from src.market_item_analysis.program_logging import LogFile, LogsHandler, log_errors
from src.market_item_analysis.shared.enums.item_enums import AffixType, EquipmentCategory
from src.market_item_analysis.shared.enums.trade_enums import ModClass, Currency, Rarity
from src.market_item_analysis.official_poe_api.api_response_parser import ApiResponseParser
from ..instances_and_definitions.item_instances import ItemRequirements, ItemTypes, ListingMetadata, ItemMods, Price, ItemProperties

parse_log = LogsHandler().fetch_log(LogFile.API_PARSING)


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


class ListingBuilder:

    def build_listing(self, rp: ApiResponseParser):

        item_mods = ItemMods(
            implicits=[mod for mod in item_mods_list if mod.mod_class == ModClass.IMPLICIT],
            enchants=[mod for mod in item_mods_list if mod.mod_class == ModClass.ENCHANT],
            fractures=[mod for mod in item_mods_list if mod.mod_class == ModClass.FRACTURED],
            explicits=[mod for mod in item_mods_list if mod.mod_class == ModClass.EXPLICIT],
        )

        item_price = Price(
            currency=Currency(rp.price_currency),
            currency_amount=rp.price_amount,
            gold_cost=rp.gold_cost
        )

        metadata = ListingMetadata(
            poster_account_name=rp.account_name,
            listing_id=rp.listing_id,
            date_posted=rp.date_fetched,
            date_fetched=datetime.now()
        )

        item_requirements = ItemRequirements(
            player_level=rp.level_requirement,
            strength=rp.strength_requirement,
            intelligence=rp.intelligence_requirement,
            dexterity=rp.dexterity_requirement
        )

        item_skills = _SkillsFactory.create_skills(rp)

        item_category = _EquipmentCategorizer.categorize(base_category=rp.base_category,
                                                         base_name=rp.base_name,
                                                         strength_requirement=rp.strength_requirement,
                                                         dexterity_requirement=rp.dexterity_requirement,
                                                         intelligence_requirement=rp.intelligence_requirement)
        item_types = ItemTypes(
            base_name=rp.base_name,
            item_category=item_category
        )

        item_properties = ItemProperties(
            rarity=Rarity(rp.rarity),
            ilvl=rp.ilvl,
            identified=rp.is_identified,
            corrupted=rp.is_corrupted,
            quality=rp.quality
        )

        listing = EquipmentListing(
            internal_id=f"LST_{uuid.uuid4().hex[:10].upper()}",
            metadata=metadata,
            item_name=rp.item_name,
            types=item_types,
            requirements=item_requirements,
            mods=item_mods,
            price=item_price,
            skills=item_skills,
            properties=item_properties
        )

        return listing


class _ModFactory:

    _mod_abbrev_d = {
        ModClass.IMPLICIT: 'implicit',
        ModClass.ENCHANT: 'enchant',
        ModClass.EXPLICIT: 'explicit',
        ModClass.FRACTURED: 'fractured',
        ModClass.RUNE: 'rune'
    }

    @staticmethod
    def create_mods(rp: ApiResponseParser) -> list[ItemMod]:


class _SkillsFactory:

    @staticmethod
    def create_skills(rp: ApiResponseParser) -> list[ItemSkill]:
        if not rp.skills_data:
            return []

        skills = []
        for skill_data in rp.skills_data:
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
