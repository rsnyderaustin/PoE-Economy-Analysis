from src.market_item_analysis.ai_modeling.config.listing_schema import ListingColumn
from src.market_item_analysis.ai_modeling.config.normalization import NormalizationConfig
from src.market_item_analysis.ai_modeling.config.poe_league import PoeLeague
from src.market_item_analysis.core.dictionary_service import DictionaryService
from src.market_item_analysis.core.enums.equipment import EquipmentStat
from src.market_item_analysis.core.string_service import StringService
from src.market_item_analysis.listing.objects import Listing


class ListingAdapter:

    @classmethod
    def to_features_vector(cls, listing: Listing) -> dict:
        d = dict()

        d.update(
            {
                ListingColumn.PRICE_CURRENCY.value: listing.price.currency.value,
                ListingColumn.PRICE_AMOUNT.value: listing.price.currency_amount
            }
        )

        d[ListingColumn.DAYS_SINCE_LEAGUE_START.value] = (listing.metadata.date_posted - PoeLeague.LEAGUE_START).days

        d[ListingColumn.EQUIPMENT_CATEGORY.value] = listing.item.category.value

        d.update(DictionaryService.convert_to_dict(listing.item.item_attributes))

        d.update({stat.stat.value: stat.value for stat in listing.item.stats.stats})

        mods_d = dict()
        for mod in listing.item.mods.mods:
            extracted = StringService.extract_numbers(
                s=mod.description,
                replacement=NormalizationConfig.MOD_NUMBER_SUB
            )
            mod_attribute = NormalizationConfig.mod_attribute_name(extracted_mod=extracted)
            mods_d[mod_attribute] = sum(extracted.numbers) / len(extracted.numbers)
        d.update(mods_d)

        skills_d = dict()
        for skill in listing.item.skills.skills:
            skill_attribute = NormalizationConfig.skill_attribute_name(skill=skill)
            skills_d[skill_attribute] = skill.level
        d.update(skills_d)

        return d


