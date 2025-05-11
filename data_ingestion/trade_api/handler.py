from datetime import datetime
import logging
import math
from collections import deque
from copy import deepcopy

from file_management import FilesManager, FileKey
from shared import shared_utils
from . import query_construction
from .query import Query, MetaFilter
from .trade_items_fetcher import TradeItemsFetcher


class FilterSplitter:

    @staticmethod
    def _split_range_into_parts(value_range: tuple, num_parts: int):
        start, end = value_range
        step = (end - start + 1) // num_parts
        ranges = [(start + i * step, min(start + (i + 1) * step - 1, end)) for i in range(num_parts)]

        # Handle any remaining range that was not perfectly divisible
        if ranges[-1][1] < end:
            ranges[-1] = (ranges[-1][0], end)

        return ranges

    @classmethod
    def split_filter(cls, n_items: int, meta_filter: MetaFilter) -> list[MetaFilter] | None:
        filter_copy = deepcopy(meta_filter)
        filter_range = cls._fetch_filter_range(filter_copy)

        if not filter_range:
            return

        if filter_range[0] == filter_range[1]:
            return
        logging.info(f"Original {meta_filter.filter_type} value: {filter_range}")

        # Can only split as many whole numbers are within the range
        num_parts = min(math.floor(n_items / 100), (filter_range[1] + 1 - filter_range[0]))

        ranges = cls._split_range_into_parts(filter_range, num_parts=num_parts)
        logging.info(f"\tFor query response with {n_items} responses:"
                     f"\t\tOriginal {meta_filter.filter_type} value: {filter_range}"
                     f"\t\tSplit {meta_filter.filter_type} into {ranges}")

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


class TradeApiHandler:

    def __init__(self):
        self.fetcher = TradeItemsFetcher()
        self.fetch_data = FilesManager().file_data[FileKey.LISTING_FETCHES]
        self.files_manager = FilesManager()

        self.split_threshold = 175

        self.valid_responses_found = 0
        self.program_start = datetime.now()

    def process_queries(self, queries: list[Query]):
        for i, query in enumerate(queries):
            logging.info(f"Processing query {i} of {len(queries)} queries.")
            yield from self.process_query(query)

    def _process_raw_response(self, response: dict):
        fetch_date = shared_utils.today_date()

        valid_responses = [api_response for api_response in response['responses']
                           if api_response['id'] not in self.fetch_data[fetch_date]]
        self.valid_responses_found += len(valid_responses)
        minutes_since_start = (datetime.now() - self.program_start).seconds / 60
        logging.info(f"{len(valid_responses)} valid responses found out of {len(response['responses'])} total responses."
                     f"\n\tHave found {self.valid_responses_found} valid responses in {round(minutes_since_start, 1)} "
                     f"minutes.")

        # The valid responses are the only ones with un-cached listing IDs, so we just cache those
        listing_ids = set(response['id'] for response in valid_responses)
        self.files_manager.cache_api_fetch_date(listing_ids=listing_ids,
                                                fetch_date=fetch_date)
        return valid_responses

    def process_query(self, query: Query):
        fetch_date = shared_utils.today_date()
        if fetch_date not in self.fetch_data:
            self.fetch_data[fetch_date] = set()

        query_dict = query_construction.create_trade_query(query=query)

        raw_response = self.fetcher.fetch_items_response(query_dict)
        total_raw_responses = raw_response['total']
        valid_responses = self._process_raw_response(response=raw_response)
        if not valid_responses:
            return

        yield valid_responses

        # If we didn't fetch a ton of raw responses then just end the query
        if total_raw_responses < self.split_threshold:
            logging.info(f"Only fetched {len(valid_responses)} from initial query. Will not split. Returning.")
            return

        for i in list(range(len(query.meta_filters))):
            query_copy = deepcopy(query)
            filter_splits = FilterSplitter.split_filter(n_items=total_raw_responses, meta_filter=query.meta_filters[i])
            if not filter_splits:
                continue

            for new_filter in filter_splits:
                query_copy.meta_filters[i] = new_filter
                query_dict = query_construction.create_trade_query(query=query_copy)
                raw_response = self.fetcher.fetch_items_response(query_dict)
                valid_responses = self._process_raw_response(response=raw_response)
                if not valid_responses:
                    continue

                yield valid_responses

