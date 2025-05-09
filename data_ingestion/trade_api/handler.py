import json
import logging
import math
from collections import deque
from copy import deepcopy
from datetime import datetime
from pathlib import Path

import pytz

from shared import PathProcessor, shared_utils
from file_management import FilesManager, FileKey
from . import query_construction
from .query import Query, MetaFilter
from .trade_items_fetcher import TradeItemsFetcher
from .. import utils


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
        logging.info(f"\tSplit {meta_filter.filter_type} into {ranges}")

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
        self.listing_fetch_dates = FilesManager().file_data[FileKey.LISTING_FETCHES]

        self.split_threshold = 175

    def _cache_listing_pulls(self, listing_ids: set[int], date_fetched: str):
        if date_fetched not in self.listing_fetch_dates:
            self.listing_fetch_dates[date_fetched] = set()

        self.listing_fetch_dates[date_fetched].update(listing_ids)

    def _determine_valid_item_responses(self, item_responses):
        date_fetched = shared_utils.today_date()
        valid_responses = []
        for ir in item_responses:
            listing_id = ir['id']

            if date_fetched not in self.listing_fetch_dates:
                self.listing_fetch_dates[date_fetched] = set()

            if listing_id in self.listing_fetch_dates[date_fetched]:
                continue

            self.listing_fetch_dates[date_fetched].add(listing_id)
            valid_responses.append(ir)

        logging.info(f"Found {len(valid_responses)} valid item responses to return.")
        return valid_responses

    def process_queries(self, queries: list[Query]):
        for query in queries:
            yield from self.process_query(query)

    def _process_response(self, response, date_fetched: str):
        valid_responses = self._determine_valid_item_responses(response['result'])
        if not valid_responses:
            return []

        num_items = response['total']
        self._cache_listing_pulls(listing_ids=set(r['id'] for r in valid_responses),
                                  date_fetched=date_fetched)
        logging.info(f"Returning {len(valid_responses)} valid of {num_items} total API item responses.")
        return valid_responses

    def process_query(self, query: Query):

        query_dict = query_construction.create_trade_query(query=query)
        response = self.fetcher.fetch_items_response(query_dict)
        valid_responses = self._process_response(response,
                                                 date_fetched=shared_utils.today_date())
        yield valid_responses

        num_items = response['total']
        if num_items < self.split_threshold:
            return

        valid_response_goal_per_query = len(valid_responses) * 0.25
        for i in list(range(len(query.meta_filters))):
            valid_response_counts = deque(maxlen=3)
            query_copy = deepcopy(query)
            filter_splits = FilterSplitter.split_filter(n_items=num_items, meta_filter=query.meta_filters[i])
            if not filter_splits:
                continue

            for new_filter in filter_splits:
                query_copy.meta_filters[i] = new_filter
                query_dict = query_construction.create_trade_query(query=query_copy)
                response = self.fetcher.fetch_items_response(query_dict)
                valid_responses = self._process_response(response=response,
                                                         date_fetched=shared_utils.today_date())
                yield valid_responses

                valid_response_counts.append(len(valid_responses))
                # If we're not getting many valid responses from the split then just continue to the next potential query split
                if sum(valid_response_counts) / len(valid_response_counts) < valid_response_goal_per_query:
                    continue
