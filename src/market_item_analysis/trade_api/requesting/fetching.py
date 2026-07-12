
import logging
from dataclasses import dataclass
from datetime import datetime
import os

import requests

from src.market_item_analysis.trade_api.requesting.request_throttler import RequestThrottler
from src.market_item_analysis.trade_api.api_result import TradeApiResult

logger = logging.getLogger(__name__)

def chunk_list(result_ids: list, chunk_size: int = 10):
    return [result_ids[i:i + chunk_size] for i in range(0, len(result_ids), chunk_size)]

def get_trade_headers() -> dict:
    return {
        'Content-Type': 'application/json',
        # Used to be '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0',
        'Cookie': f'POESESSID={os.getenv("POSSESSID")}',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'www.pathofexile.com',
        'Origin': 'https://www.pathofexile.com',
        'Referer': 'https://www.pathofexile.com/trade2/search/poe2/Fate%20of%20the%20Vaal'
    }


class _TradePoster:

    _BASE_URL = "https://www.pathofexile.com/api/trade2/search/poe2/Fate%20of%20the%20Vaal"
    _ENDPOINT = "fetch"
    _FILENAME_STARTER = '/official_api/trade2/fetch/'

    _REQUEST_THROTTLER = RequestThrottler()

    @classmethod
    def post(cls, query):
        response = cls._REQUEST_THROTTLER.send_request(
            request_func=requests.post,
            url=cls._BASE_URL,
            headers=get_trade_headers(),
            json=query
        )
        response.raise_for_status()
        json_data = response.json()

        return _TradePostResponse(json_data)

class _TradeGetter:

    _BASE_URL = "https://www.pathofexile.com/api/trade2/fetch/"

    _COOKIES = {
        'POSSESSID': os.getenv("POSSESSID")
    }

    _REQUEST_THROTTLER = RequestThrottler()

    @classmethod
    def get(cls, search_id: str, result_ids: list[str]) -> dict:
        params = {
            'query': search_id,
            'realm': 'poe2'
        }

        url = f"{cls._BASE_URL}{','.join(result_ids)}"

        response = cls._REQUEST_THROTTLER.send_request(
            request_func=requests.get,
            url=url,
            headers=get_trade_headers(),
            params=params,
            cookies=cls._COOKIES
        )
        response.raise_for_status()
        json_data = response.json()

        return json_data

class _TradePostResponse:

    def __init__(self, response_json: dict):
        self.search_id = response_json['id']
        self.result_ids = response_json['result']
        self.total_possible_responses = response_json['total']


@dataclass(frozen=True)
class TradeApiResultsResponse:
    results: list[TradeApiResult]
    total_results: int

    @property
    def results_count(self):
        return len(self.results)

class TradeApiResultsFetcher:

    @classmethod
    def fetch(cls, query) -> tuple[list[dict], int]:
        post_response = _TradePoster.post(query=query)

        item_id_chunk_lists = chunk_list(result_ids=post_response.result_ids, chunk_size=10)

        response_items = []
        for result_ids_list in item_id_chunk_lists:
            get_json = _TradeGetter.get(
                search_id=post_response.search_id,
                result_ids=result_ids_list
            )
            result = get_json['result']
            response_items.extend(result)

        return response_items, post_response.total_possible_responses
