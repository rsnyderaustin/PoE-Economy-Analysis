import math
from copy import deepcopy
from datetime import datetime
from typing import Generator
import logging

from src.market_item_analysis.trade_api.requesting.fetching import TradeApiResultsFetcher, TradeApiResultsResponse
from src.market_item_analysis.trade_api.query.builder import TradeApiQueryBuilder
from src.market_item_analysis.trade_api.query.objects import TradeApiQueryPlan, TradeApiMetaFilter
from src.market_item_analysis.core.types import RangeService
from src.market_item_analysis.trade_api.api_result import TradeApiResult

logger = logging.getLogger(__name__)


class FilterService:

    @classmethod
    def split_meta_filter(cls, trade_results_count: int, meta_filter: TradeApiMetaFilter) -> list[TradeApiMetaFilter] | None:
        """
        Evenly splits a singular query filter (ex: price range) into separate parts. This is used when
        we fetch too many results and have to split up the query to capture all possible results.
        """
        if not meta_filter.splittable:
            raise TypeError(f"Cannot split MetaFilter of type {type(meta_filter)}")

        val_range = meta_filter.values_range

        if val_range.is_point:
            raise ValueError(f"Cannot split MetaFilter when it's a point. Values range: {val_range}")

        # Can only split as many whole numbers are within the range
        number_of_parts = min(math.floor(trade_results_count / 100), val_range.values_count)

        split_ranges = RangeService.split(r=val_range,
                                          number_of_parts=number_of_parts)

        logger.info(f"{trade_results_count} results split {type(meta_filter)} from {str(val_range)} into "
                    f"{' | '.join([str(split_range) for split_range in split_ranges])}")

        split_filters = []
        for split_range in split_ranges:
            split_copy = deepcopy(meta_filter)
            split_copy.values_range = split_range
            split_filters.append(split_copy)

        return split_filters

class TradeApiInterface:

    @classmethod
    def fetch_responses(cls,
                        query_plan: TradeApiQueryPlan,
                        total_results_exit_threshold: int | None = 175) -> Generator[TradeApiResultsResponse, None, None]:
        query = TradeApiQueryBuilder.build(query_plan=query_plan)
        raw_results, total_results = TradeApiResultsFetcher.fetch(query)

        if total_results == 0:
            return

        result_objs = [TradeApiResult.from_dict(d=result_d) for result_d in raw_results]

        response_obj = TradeApiResultsResponse(
            results=result_objs,
            total_results=total_results
        )
        yield response_obj

        if total_results < total_results_exit_threshold:
            logger.info(f"Fetched {total_results} from initial query. Will not split. Returning.")
            return

        for meta_filter in query_plan.meta_filters:
            if not meta_filter.splittable:
                continue

            filter_splits = FilterService.split_meta_filter(trade_results_count=total_results,
                                                            meta_filter=meta_filter)
            for split_filter in filter_splits:
                query_plan_copy = deepcopy(query_plan)
                query_plan_copy.clone_with_new_filter(original_filter=meta_filter, new_filter=split_filter)
                for api_response in cls.fetch_responses(query_plan_copy):
                    yield api_response
