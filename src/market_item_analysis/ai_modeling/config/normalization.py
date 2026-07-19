from src.market_item_analysis.core.string_service import NumbersExtractedString
from src.market_item_analysis.listing.objects import Skill


class NormalizationConfig:

    MOD_NUMBER_SUB = 'n'

    @classmethod
    def mod_attribute_name(cls, extracted_mod: NumbersExtractedString):
        return f"mod_{extracted_mod.substituted_string}"

    @classmethod
    def skill_attribute_name(cls, skill: Skill):
        return f"skill_{skill.name}"
