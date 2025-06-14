
from datetime import datetime

import requests

from core import env_loader
from program_logging import LogsHandler, LogFile, log_errors
from trade_api.request_throttler import RequestThrottler

api_log = LogsHandler().fetch_log(LogFile.EXTERNAL_APIS)


def chunk_list(items: list, chunk_size: int = 10):
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


class TradeItemsFetcher:

    post_url = "https://www.pathofexile.com/api/trade2/search/poe2/Dawn%20of%20the%20Hunt"
    get_url = "https://www.pathofexile.com/api/trade2/fetch/"

    post_endpoint = "fetch"
    post_filename_starter = '/official_api/trade2/fetch/'

    headers = {
        'Content-Type': 'application/json',
        # Used to be '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) Gecko/20100101 Firefox/138.0',
        'Cookie': f'POESESSID={env_loader.get_env("POSSESSID")}',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'www.pathofexile.com',
        'Origin': 'https://www.pathofexile.com',
        'Referer': 'https://www.pathofexile.com/trade2/search/poe2/Dawn%20of%20the%20Hunt'
    }

    request_throttler = RequestThrottler()

    items_fetched = 0
    class_start = datetime.now()

    @classmethod
    @log_errors(api_log)
    def _post_for_search_id(cls, query):
        response = cls.request_throttler.send_request(
            request_func=requests.post,
            url=cls.post_url,
            headers=cls.headers,
            json=query
        )
        response.raise_for_status()
        json_data = response.json()

        return json_data

    @classmethod
    @log_errors(api_log)
    def _get_with_item_ids(cls, post_response, item_ids) -> list:
        chunked_list = chunk_list(items=item_ids, chunk_size=10)

        params = {
            'query': post_response['id'],
            'realm': 'poe2'
        }

        response_items = []
        for chunked_ids in chunked_list:
            chunked_ids = ",".join(chunked_ids)

            get_url = f'{cls.get_url}{chunked_ids}'

            cookies = {
                'POSSESSID': env_loader.get_env("POSSESSID")
            }
            response = cls.request_throttler.send_request(
                request_func=requests.get,
                url=get_url,
                headers=cls.headers,
                params=params,
                cookies=cookies
            )
            response.raise_for_status()
            json_data = response.json()
            result = json_data['result']
            response_items.extend(result)

        return response_items

    @classmethod
    def fetch_items_response(cls, query) -> tuple[list, int]:
        post_response = cls._post_for_search_id(query=query)

        total_responses = post_response['total']
        item_ids = post_response['result']

        get_response = cls._get_with_item_ids(post_response=post_response,
                                              item_ids=item_ids)
        return get_response, total_responses
