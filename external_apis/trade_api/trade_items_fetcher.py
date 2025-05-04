
import logging

import requests

from external_apis.trade_api.request_throttler import RequestThrottler
from shared import EnvLoader
from shared.enums import EnvVar


def chunk_list(items: list, chunk_size: int = 10):
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


class TradeItemsFetcher:

    post_url = "https://www.pathofexile.com/api/trade2/search/poe2/Dawn%20of%20the%20Hunt"
    get_url = "https://www.pathofexile.com/api/trade2/fetch/"

    post_endpoint = "fetch"
    post_filename_starter = '/official_api/trade2/fetch/'

    possess_id = EnvLoader.get_env(env_variable=EnvVar.POSSESSID)
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'Cookie': f'POESESSID={possess_id}',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Host': 'www.pathofexile.com',
        'Origin': 'https://www.pathofexile.com',
        'Referer': 'https://www.pathofexile.com/trade2/search/poe2/Dawn%20of%20the%20Hunt'
    }

    request_throttler = RequestThrottler()

    @classmethod
    def _post_for_search_id(cls, query):

        logging.info("Fetching item IDs.")
        response = cls.request_throttler.send_request(
            request_func=requests.post,
            url=cls.post_url,
            headers=cls.headers,
            json=query
        )
        response.raise_for_status()
        json_data = response.json()
        logging.info(f"Successfully fetched {len(json_data['result'])} item IDs")
        return json_data

    @classmethod
    def _get_with_item_ids(cls, search_id, item_ids) -> list:

        logging.info(f"Getting things with item IDs..")
        chunked_list = chunk_list(items=item_ids, chunk_size=10)

        params = {
            'query': search_id,
            'realm': 'poe2'
        }

        response_items = []
        for chunked_ids in chunked_list:
            chunked_ids = ",".join(chunked_ids)

            get_url = f'{cls.get_url}{chunked_ids}'

            cookies = {
                'POSSESSID': cls.possess_id
            }
            response = cls.request_throttler.send_request(
                request_func=requests.get,
                url=get_url,
                headers=cls.headers,
                params=params,
                cookies=cookies
            )
            response.raise_for_status()
            logging.info("Successfully sent a GET for things with item IDs.")
            json_data = response.json()
            result = json_data['result']
            response_items.extend(result)

        return response_items

    @classmethod
    def fetch_items(cls, query):
        post_response = cls._post_for_search_id(query=query)
        search_id = post_response['id']
        item_ids = post_response['result']

        get_response = cls._get_with_item_ids(search_id=search_id,
                                              item_ids=item_ids)
        return get_response


