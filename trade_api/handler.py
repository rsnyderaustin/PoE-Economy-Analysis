import math
from copy import deepcopy
from datetime import datetime
from typing import Generator

from shared import shared_utils
from program_logging import LogsHandler, LogFile
from . import query_construction
from .query import Query, MetaFilter
from .trade_items_fetcher import TradeItemsFetcher

api_log = LogsHandler().fetch_log(LogFile.EXTERNAL_APIS)


class _FilterSplitter:

    @staticmethod
    def _split_range_into_parts(value_range: tuple, num_parts: int) -> list[tuple]:
        start, end = value_range

        if start == end:
            return [(start, end)]

        num_values = end + 1 - start

        # We need to have at least one for a step value
        iterative_value = max(round(num_values / num_parts), 1) - 1

        current_min = start
        ranges = []
        for step in range(num_values):
            min_ = current_min
            max_ = current_min + iterative_value

            if max_ > end:
                if min_ > end:
                    break

                new_range = min_, end
                ranges.append(new_range)
                break

            new_range = min_, max_
            ranges.append(new_range)

            current_min = max_ + 1

        """
        Below just ensures that the very last range covers until the end of the 
        values range parameter
        """
        last_range = ranges[len(ranges) - 1]
        last_range = last_range[0], end
        ranges[len(ranges) - 1] = last_range

        return ranges

    @classmethod
    def split_filter(cls, n_items: int, meta_filter: MetaFilter) -> list[MetaFilter] | None:
        """
        Evenly splits a singular query filter (ex: price range) into separate parts. This is used when
        we fetch too many results and have to split up the query to capture all possible results.
        """
        filter_copy = deepcopy(meta_filter)
        filter_range = cls._fetch_filter_range(filter_copy)

        if not filter_range:
            return

        if filter_range[0] == filter_range[1]:
            return

        # Can only split as many whole numbers are within the range
        num_parts = min(math.floor(n_items / 100), (filter_range[1] + 1 - filter_range[0]))

        ranges = cls._split_range_into_parts(filter_range, num_parts=num_parts)
        api_log.info(f"{n_items} responses split {meta_filter.filter_type} from {filter_range} into {ranges}")

        filters = []
        for value_range in ranges:
            new_copy = deepcopy(filter_copy)

            if len(new_copy.filter_value) == 2:
                new_copy.filter_value = value_range
            elif new_copy.currency_amount and len(new_copy.currency_amount) == 2:
                new_copy.currency_amount = value_range

            filters.append(new_copy)

        return filters

    @staticmethod
    def _fetch_filter_range(meta_filter: MetaFilter):
        if len(meta_filter.filter_value) == 2:
            return meta_filter.filter_value
        elif meta_filter.currency_amount and len(meta_filter.currency_amount) == 2:
            return meta_filter.currency_amount

        return None


def _key_response(listing_id, date_fetched: str):
    return f"listing_{listing_id}_fetched_{date_fetched}"


class TradeApiHandler:

    def __init__(self):
        self.fetcher = TradeItemsFetcher()

        self.split_threshold = 175

        self.program_start = datetime.now()

    def fetch_responses(self, queries: list[Query]) -> Generator[list[dict], None, None]:
        for i, query in enumerate(queries):
            api_log.info(f"Processing query {i + 1} of {len(queries)} queries.")
            print(f"Processing query {i + 1} of {len(queries)} queries.")
            for responses, response_results_count in self._process_query(query):
                responses = [shared_utils.sanitize_dict_texts(response) for response in responses]
                yield responses

    def _process_query(self, query: Query):
        query_dict = query_construction.create_trade_query(query=query)

        responses, response_results_count = self.fetcher.fetch_items_response(query_dict)

        if not responses:
            return

        yield responses, response_results_count

        # If we didn't fetch a ton of raw responses then just end the query
        if response_results_count < self.split_threshold:
            api_log.info(f"Only fetched {len(responses)} from initial query. Will not split. Returning.")
            return

        for i in list(range(len(query.meta_filters))):
            query_copy = deepcopy(query)
            filter_splits = _FilterSplitter.split_filter(n_items=response_results_count, meta_filter=query.meta_filters[i])
            if not filter_splits:  # Skip if we weren't able to split this filter up into parts
                continue

            # For each split portion of the metafilter, insert the split portion into the copied query and fetch those results
            for new_filter in filter_splits:
                query_copy.meta_filters[i] = new_filter
                query_dict = query_construction.create_trade_query(query=query_copy)
                responses, response_results_count = self.fetcher.fetch_items_response(query_dict)

                if not responses:
                    continue

                yield responses, response_results_count
