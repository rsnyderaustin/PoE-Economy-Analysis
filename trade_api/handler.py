import logging
import math
from copy import deepcopy
from datetime import datetime

from file_management import FilesManager, DataPath
from shared import shared_utils
from . import query_construction
from .query import Query, MetaFilter
from .trade_items_fetcher import TradeItemsFetcher


class FilterSplitter:

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


def _determine_valid_responses(response: dict, fetch_date_record: dict, raw_listings: list):
    fetch_date = shared_utils.today_date()
    if fetch_date not in fetch_date_record:
        fetch_date_record[fetch_date] = set()

    valid_responses = [api_response for api_response in response['responses']
                       if api_response['id'] not in fetch_date_record[fetch_date]]
    raw_listings.extend(valid_responses)  # Save to file

    valid_listing_ids = set(response['id'] for response in valid_responses)
    fetch_date_record[fetch_date].update(valid_listing_ids)  # Save to file

    return valid_responses


class TradeApiHandler:

    def __init__(self):
        self.fetcher = TradeItemsFetcher()
        self.files_manager = FilesManager()
        self.fetch_date_record = self.files_manager.file_data[DataPath.LISTING_FETCH_DATES]
        self.raw_listings = self.files_manager.file_data[DataPath.RAW_LISTINGS]

        self.split_threshold = 175

        self.total_valid_responses = 0

        self.program_start = datetime.now()

    def _log_responses_progress(self, valid_query_responses, total_query_responses):
        minutes_since_start = round((datetime.now() - self.program_start).seconds / 60, 1)
        logging.info(f"\n\tTrade API total responses: {total_query_responses}"
                     f"\n\tTrade API valid responses: {valid_query_responses}"
                     f"\n\tTotal valid responses in {minutes_since_start} minutes: {self.total_valid_responses}")

    def process_queries(self, queries: list[Query]):
        for i, query in enumerate(queries):
            logging.info(f"Processing query {i + 1} of {len(queries)} queries.")
            valid_query_responses = 0
            total_query_responses = 0
            for responses, raw_responses in self._process_query(query):
                self.total_valid_responses += len(responses)
                valid_query_responses += len(responses)
                total_query_responses += raw_responses
                yield responses

            self._log_responses_progress(valid_query_responses=valid_query_responses,
                                         total_query_responses=total_query_responses)
            self.files_manager.save_data(paths=[DataPath.RAW_LISTINGS, DataPath.LISTING_FETCH_DATES])

    def _process_query(self, query: Query):
        query_dict = query_construction.create_trade_query(query=query)

        raw_response = self.fetcher.fetch_items_response(query_dict)
        total_raw_responses = raw_response['total']
        valid_responses = _determine_valid_responses(response=raw_response,
                                                     fetch_date_record=self.fetch_date_record,
                                                     raw_listings=self.raw_listings)
        if not valid_responses:
            return

        yield valid_responses, total_raw_responses

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
                valid_responses = _determine_valid_responses(response=raw_response,
                                                             fetch_date_record=self.fetch_date_record,
                                                             raw_listings=self.raw_listings)

                if not valid_responses:
                    continue

                yield valid_responses, total_raw_responses

