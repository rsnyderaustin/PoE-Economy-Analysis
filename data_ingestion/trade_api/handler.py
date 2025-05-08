import json
import logging
import math
from collections import deque
from copy import deepcopy
from pathlib import Path

import pandas as pd

from shared import PathProcessor
from .query import Query, MetaFilter
from .query_construction import create_trade_query
from .trade_items_fetcher import TradeItemsFetcher
from .. import utils


def _apply_create_listing_id_history(row, listing_id_history: dict):
    listing_id = row['listing_id']
    listing_date = row['date_fetched']

    if listing_date not in listing_id_history:
        listing_id_history[listing_date] = set()

    listing_id_history[listing_date].add(listing_id)


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

        # Can only split as many whole numbers are within the range
        num_parts = min(math.floor(n_items / 100), (filter_range[1] + 1 - filter_range[0]))

        ranges = cls._split_range_into_parts(filter_range, num_parts=num_parts)

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

        fetch_dates_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('xgboost_model/training_data/listing_fetch_dates.json')
            .path
        )
        with open(fetch_dates_json_path, 'r') as fetch_dates_file:
            self.listing_fetch_dates = json.load(fetch_dates_file)

        self.split_threshold = 175

    def _determine_valid_item_responses(self, item_responses):
        valid_responses = []
        for ir in item_responses:
            listing_id = ir['id']
            datetime_fetched = ir['listing']['indexed']
            date_fetched = utils.extract_date(datetime_fetched)

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

    def process_query(self, query: Query):

        query_dict = create_trade_query(query=query)
        response = self.fetcher.fetch_items_response(query_dict)
        valid_responses = self._determine_valid_item_responses(response['result'])
        logging.info(f"Returning {len(valid_responses)} valid API item responses.")
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
                query_dict = create_trade_query(query=query)
                response = self.fetcher.fetch_items_response(query_dict)
                valid_responses = self._determine_valid_item_responses(response['result'])
                logging.info(f"Returning {len(valid_responses)} valid API item responses.")
                yield valid_responses

                valid_response_counts.append(len(valid_responses))
                if sum(valid_response_counts) / len(valid_response_counts) < valid_response_goal_per_query:
                    return
