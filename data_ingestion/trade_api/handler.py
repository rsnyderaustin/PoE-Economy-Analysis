import json
from pathlib import Path

import pandas as pd

from .query import Query
from .trade_items_fetcher import TradeItemsFetcher
from .query_construction import create_trade_query

from shared import PathProcessor


def _apply_create_listing_id_history(row, listing_id_history: dict):
    listing_id = row['listing_id']
    listing_date = row['date_fetched']

    if listing_date not in listing_id_history:
        listing_id_history[listing_date] = set()

    listing_id_history[listing_date].add(listing_id)


def _refit_range(n_items: int, original_query: Query):
    for meta_filter in original_query.meta_filters:
        if isinstance(meta_filter.filter_value, tuple):



class TradeApiHandler:

    def __init__(self):
        self.fetcher = TradeItemsFetcher()

        training_data_json_path = (
            PathProcessor(Path.cwd())
            .attach_file_path_endpoint('xgboost_model/training_data/listings.json')
            .path
        )
        with open(training_data_json_path, 'r') as training_data_file:
            training_data = json.load(training_data_file)

        df = pd.DataFrame(training_data)
        self.loaded_dates = dict()
        self.loaded_dates = df.apply(_apply_create_listing_id_history, axis=1, args=(self.loaded_dates,))

    def query(self, queries: list[Query]):
        for query in queries:
            query_dict = create_trade_query(query=query)
            response = self.fetcher.fetch_items_response(query_dict)
            num_items = response['total']

            # Queries are limited to 100 items; exceeding this means significant data loss
            if num_items >= 175:


