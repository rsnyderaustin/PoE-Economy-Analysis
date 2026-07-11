
from src.market_item_analysis.trade_api.query.objects import TradeApiQuery, TradeApiQueryPlan


class TradeApiQueryBuilder:

    @classmethod
    def build(cls, query_plan: TradeApiQueryPlan) -> TradeApiQuery:
        query = TradeApiQuery()

        for meta_filter in query_plan.meta_filters:
            query.insert_value(entry=meta_filter.query_entry)

        for stat_filter_group in query_plan.stat_filters_groups:
            query.insert_value(entry=stat_filter_group.query_entry)

        return query


