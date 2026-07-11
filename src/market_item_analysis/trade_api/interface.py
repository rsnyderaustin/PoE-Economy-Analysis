import math
from copy import deepcopy
from datetime import datetime
from typing import Generator
import logging

from .fetching import TradeApiResultsFetcher, TradeApiResultsResponse
from .query.construction import TradeApiQueryBuilder
from .query.query import QueryPlan, MetaFilter, RangeMetaFilter
from ..core.types import RangeService

logger = logging.getLogger(__name__)


class FilterService:

    @classmethod
    def split_meta_filter(cls, trade_results_count: int, meta_filter: MetaFilter) -> list[MetaFilter] | None:
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

    def __init__(self, total_results_exit_threshold: int | None = None):
        self.total_results_exit_threshold = total_results_exit_threshold or 175

        self.program_start = datetime.now()

    def fetch_responses(self, query_plan: QueryPlan) -> Generator[TradeApiResultsResponse, None, None]:
        query = TradeApiQueryBuilder.build(query_plan=query_plan)
        api_response = TradeApiResultsFetcher.fetch(query)

        if api_response.results_count == 0:
            return

        yield api_response

        if api_response.total_results < self.total_results_exit_threshold:
            logger.info(f"Fetched {api_response.total_results} from initial query. Will not split. Returning.")
            return

        for meta_filter in query_plan.meta_filters:
            if not meta_filter.splittable:
                continue

            filter_splits = FilterService.split_meta_filter(trade_results_count=api_response.results_count,
                                                            meta_filter=meta_filter)
            for split_filter in filter_splits:
                query_plan_copy = deepcopy(query_plan)
                query_plan_copy.substitute_meta_filter(original_filter=meta_filter, new_filter=split_filter)
                for api_response in self.fetch_responses(query_plan_copy):
                    yield api_response
