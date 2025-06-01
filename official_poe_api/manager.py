
import json
from enum import Enum
from pathlib import Path
from urllib.parse import urljoin

import requests

from shared import shared_utils
from shared.logging import LogsHandler, LogFile

api_log = LogsHandler().fetch_log(LogFile.EXTERNAL_APIS)


class OfficialEndpoint(Enum):
    STATIC = 'static/'
    STATS = 'stats/'


class OfficialApiPuller:

    def __init__(self):
        # Input
        self.base_url = 'https://www.pathofexile.com/api/trade2/data/'

        self.headers = {
            'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
            'Referer': 'FILL_WITH_API_URL',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
        }

        self.acceptable_endpoints = ['static', 'stats']

    def _load_api_data(self, api_url):
        api_log.info(f"Loading stat modifiers from PoE API at url {api_url}")
        headers = self.headers
        headers['Referer'] = api_url
        response = requests.get(url=api_url,
                                headers=headers)
        response.raise_for_status()
        api_log.info("\tSuccessfully loaded stat modifiers from PoE API.")

        json_data = response.json()
        return json_data

    def _verify_endpoint(self, endpoint: str):
        if endpoint not in self.acceptable_endpoints:
            raise ValueError(f"Endpoint {endpoint} not one of acceptable values {self.acceptable_endpoints}.")

    @staticmethod
    def _format_static_data(data: dict):

        item_blocks = data['result']

        returnable_dict = dict()
        for item_block in item_blocks:
            item_block_name = item_block['id']
            returnable_dict[item_block_name] = list()

            for entry in item_block['entries']:
                entry = entry
                if (not entry['id'] or len(entry['id']) == 0
                        or not entry['text'] or len(entry['text']) == 0):
                    continue

                entry.pop('image', None)

                returnable_dict[item_block_name].append(entry)

        returnable_dict = shared_utils.sanitize_dict_texts(returnable_dict)

        return returnable_dict

    @staticmethod
    def _format_stats_data(data: dict):
        stat_blocks = data['result']

        stat_json = {
            stat_block['id']: stat_block['entries'] for stat_block in stat_blocks
        }
        stat_json = shared_utils.sanitize_dict_texts(stat_json)

        return stat_json

    def pull_data(self, endpoint: OfficialEndpoint):
        url = urljoin(self.base_url, endpoint.value)
        data = self._load_api_data(api_url=url)

        if endpoint == OfficialEndpoint.STATIC:
            data = self._format_static_data(data)
        else:
            data = self._format_stats_data(data)

        return data


