
import logging

import requests

import shared
from external_apis.trade_api.request_throttler import RequestThrottler


def chunk_list(items: list, chunk_size: int = 10):
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


class TradeItemsFetcher:

    def __init__(self):
        self.post_url = "https://www.pathofexile.com/api/trade2/search/poe2/Dawn%20of%20the%20Hunt"
        self.get_url = "https://www.pathofexile.com/api/trade2/fetch/"

        self.post_endpoint = "fetch"
        self.post_filename_starter = '/official_api/trade2/fetch/'

        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Cookie': f'POESESSID={shared.env.possess_id}',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'www.pathofexile.com',
            'Origin': 'https://www.pathofexile.com',
            'Referer': 'https://www.pathofexile.com/trade2/search/poe2/Dawn%20of%20the%20Hunt'
        }

        self.request_throttler = RequestThrottler()

    def _post_for_search_id(self, query):

        logging.info("Fetching item IDs.")
        response = self.request_throttler.send_request(
            request_func=requests.post,
            url=self.post_url,
            headers=self.headers,
            json=query
        )
        response.raise_for_status()
        json_data = response.json()
        logging.info(f"Successfully fetched {len(json_data['result'])} item IDs")
        return json_data

    def _get_with_item_ids(self, search_id, item_ids) -> list:

        logging.info(f"Getting things with item IDs..")
        chunked_list = chunk_list(items=item_ids, chunk_size=10)

        params = {
            'query': search_id,
            'realm': 'poe2'
        }

        response_items = []
        for chunked_ids in chunked_list:
            chunked_ids = ",".join(chunked_ids)

            get_url = f'{self.get_url}{chunked_ids}'

            cookies = {
                'POSSESSID': shared.env.possess_id
            }
            response = self.request_throttler.send_request(
                request_func=requests.get,
                url=get_url,
                headers=self.headers,
                params=params,
                cookies=cookies
            )
            response.raise_for_status()
            logging.info("Successfully sent a GET for things with item IDs.")
            json_data = response.json()
            result = json_data['result']
            response_items.extend(result)

        return response_items

    def fetch_items(self, query):
        post_response = self._post_for_search_id(query=query)
        search_id = post_response['id']
        item_ids = post_response['result']

        get_response = self._get_with_item_ids(search_id=search_id,
                                              item_ids=item_ids)
        return get_response


