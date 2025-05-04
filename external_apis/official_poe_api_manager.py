
import json
import logging
from enum import Enum
from pathlib import Path

import requests

from shared import PathProcessor


def _format_static_data(data: dict):

    item_blocks = data['result']

    returnable_dict = dict()
    for item_block in item_blocks:
        item_block_name = item_block['id'].lower()
        returnable_dict[item_block_name] = list()

        for entry in item_block['entries']:
            if (not entry['id'] or len(entry['id']) == 0
                    or not entry['text'] or len(entry['text']) == 0):
                continue

            if 'image' in entry:
                del entry['image']

            returnable_dict[item_block_name].append(entry)

    return returnable_dict

def _format_stats_data(data: dict):
    stat_blocks = data['result']

    stat_json = {
        stat_block['id']: stat_block['entries'] for stat_block in stat_blocks
    }

    return stat_json


class Endpoint(Enum):
    STATIC = 'static'
    STATS = 'stats'


class OfficialApiManager:

    def __init__(self):
        # Input
        base_url = 'https://www.pathofexile.com/api/trade2/data/'

        stats_input_endpoint = '/stats'
        static_input_endpoint = '/static'

        self.stats_input_path = (
            PathProcessor(
                path=base_url
            )
            .attach_url_endpoint(endpoint=stats_input_endpoint)
            .path
        )

        self.static_input_path = (
            PathProcessor(
                path=base_url
            )
            .attach_url_endpoint(endpoint=static_input_endpoint)
            .path
        )

        self.headers = {
            'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
            'Referer': 'FILL_WITH_API_URL',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
        }

        # Output
        stats_endpoint = 'external_apis/official_api/json_data/official_stats.json'
        static_endpoint = 'external_apis/official_api/json_data/official_static.json'

        self.stats_output_path = (
            PathProcessor(
                path=Path.cwd()
            )
            .attach_file_path_endpoint(endpoint=stats_endpoint)
            .path
        )
        self.static_output_path = (
            PathProcessor(
                path=Path.cwd()
            )
            .attach_file_path_endpoint(endpoint=static_endpoint)
            .get
        )

        self.acceptable_endpoints = ['static', 'stats']


    def _load_api_data(self, api_url):
        logging.info(f"Loading stat modifiers from PoE API at url {api_url}")
        headers = self.headers
        headers['Referer'] = api_url
        response = requests.get(url=api_url,
                                headers=headers)
        response.raise_for_status()
        logging.info("\tSuccessfully loaded stat modifiers from PoE API.")

        json_data = response.json()
        return json_data

    def _verify_endpoint(self, endpoint: str):
        if endpoint not in self.acceptable_endpoints:
            raise ValueError(f"Endpoint {endpoint} not one of acceptable values {self.acceptable_endpoints}.")

    def pull_data(self, endpoint: str, load_locally: bool = False):
        self._verify_endpoint(endpoint)

        endpoint = self.static_input_path if endpoint == 'static' else self.stats_input_path

        if load_locally:
            import_path = self.static_output_path if endpoint == 'static' else self.stats_output_path

            with import_path.open('r', encoding='utf-8') as static_file:
                data = json.load(static_file)
            return data
        else:
            import_url = self.static_input_path if endpoint == 'static' else self.stats_input_path
            data = self._load_api_data(api_url=import_url)

            if endpoint == 'static':
                data = _format_static_data(data)
            else:
                data = _format_stats_data(data)

            return data

    def save_data_to_json(self, endpoint: str):
        data = self.pull_data(endpoint=endpoint)
        if endpoint == 'static':
            data = _format_static_data(data)
            output_path = self.static_output_path
        else:
            data = _format_stats_data(data)
            output_path = self.stats_output_path

        with open(output_path, "w") as f:
            json.dump(data, f, indent=4)


