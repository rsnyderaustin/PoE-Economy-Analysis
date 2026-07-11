import itertools

from src.currency_arbitrage.data_objects import Currency
from src.market_item_analysis.core.enums.equipment import EquipmentCategory, Rarity
from src.market_item_analysis.core.enums.trade import TradeQueryMetaFilterDefinition, ListedSince
from src.market_item_analysis.core.types import Range
from src.market_item_analysis.trade_api.query.objects import TradeApiQueryPlan, TradeApiMetaFilter, \
    TradeApiRangeMetaFilter, TradeApiEnumMetaFilter


def standard_training_query_plans() -> list[TradeApiQueryPlan]:
    martial_weapon_categories = [cat for cat in EquipmentCategory if cat.is_martial]
    currencies = [Currency.EXALTED_ORB]

    currency_amounts = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 45, 50]
    currency_ranges = []
    for i, currency_amount in enumerate(currency_amounts[:-1]):
        currency_ranges.append(Range(currency_amount, currency_amounts[i + 1]))

    query_plans = []
    for item_category, currency, currency_range in itertools.product(martial_weapon_categories, currencies, currency_ranges):
        ilvl_filter = TradeApiRangeMetaFilter(
            filter_definition=TradeQueryMetaFilterDefinition.ITEM_LEVEL,
            values_range=Range(71, 100)
        )

        category_filter = TradeApiEnumMetaFilter(
            filter_definition=TradeQueryMetaFilterDefinition.ITEM_CATEGORY,
            enum_value=item_category
        )

        days_since_listed_filter = TradeApiEnumMetaFilter(
            filter_definition=TradeQueryMetaFilterDefinition.LISTED_SINCE,
            enum_value=ListedSince.UP_TO_1_HOUR
        )

        price_filter = TradeApiRangeMetaFilter(
            filter_definition=TradeQueryMetaFilterDefinition.LISTING_PRICE,
            values_range=currency_range
        )

        rarity_filter = TradeApiEnumMetaFilter(
            filter_definition=TradeQueryMetaFilterDefinition.ITEM_RARITY,
            enum_value=Rarity.RARE
        )

        query_plan = TradeApiQueryPlan(
            meta_filters=[ilvl_filter, category_filter, price_filter, rarity_filter, days_since_listed_filter],
            stat_filters_groups=[]
        )
        query_plans.append(query_plan)

    return query_plans
