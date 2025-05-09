
import json
import re
from pathlib import Path

import requests

from shared import PathProcessor


class PoecdApiManager:

    def __init__(self):

        # Input

        self.source_url = 'https://www.craftofexile.com/json/poe2/'

        self.bases_input_url = (
            PathProcessor(
                path=self.source_url
            )
            .attach_url_endpoint(endpoint='/lang/poec_lang.us.json?v=1744834998')
            .path
        )

        self.mods_input_url = (
            PathProcessor(
                path=self.source_url
            )
            .attach_url_endpoint(endpoint='/main/poec_data.json?v=1744834989')
            .path
        )

        self.cookies = {
            'PHPSESSID': '7p4qt447dai0mudpdmqhg763n9',
            'hbmd': '0',
            'league': '17',
            'vmode': 'd',
            'amode': 'x',
            'blkprc': 'y',
            'tagrps': 'true',
            'tafilts': 'true',
            'asmt': '1',
            'clng': 'us',
        }

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:136.0) Gecko/20100101 Firefox/136.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            # 'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Referer': 'https://www.craftofexile.com/?b=2&ob=both&v=d&a=x&l=a&lg=17&bp=y&as=1&hb=0&bld={}&im={}&ggt=|&ccp={}&gvc={%22limit%22:88}',
            # 'Cookie': 'PHPSESSID=7p4qt447dai0mudpdmqhg763n9; hbmd=0; league=17; vmode=d; amode=x; blkprc=y; tagrps=true; tafilts=true; asmt=1; clng=us',
            'Sec-Fetch-Dest': 'script',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        # Output
        bases_endpoint = '/misc/craft_of_exile_api/json_data/poecd_bases.json'
        mods_endpoint='/misc/craft_of_exile_api/json_data/poecd_stats.json'

        self.bases_json_path = (
            PathProcessor(
                path=Path.cwd()
            )
            .attach_file_path_endpoint(endpoint=bases_endpoint)
            .path
        )
        self.mods_json_path = (
            PathProcessor(
                path=Path.cwd()
            )
            .attach_file_path_endpoint(endpoint=mods_endpoint)
            .path
        )

        self.acceptable_endpoints = ['bases', 'mods']

    def _verify_endpoint(self, endpoint: str):
        if endpoint not in self.acceptable_endpoints:
            raise ValueError(f"Endpoint {endpoint} not one of acceptable values {self.acceptable_endpoints}.")

    def pull_data(self, endpoint: str, load_locally: bool = False):
        self._verify_endpoint(endpoint)

        if load_locally:
            import_path = self.mods_json_path if endpoint == 'mods' else self.bases_json_path

            with import_path.open('r', encoding='utf-8') as static_file:
                data = json.load(static_file)
            return data
        else:
            import_url = self.mods_input_url if endpoint == 'mods' else self.bases_input_url
            response = requests.get(url=import_url,
                                    headers=self.headers,
                                    cookies=self.cookies)
            response.raise_for_status()

            content = response.content.decode('utf-8')
            content = re.sub(r'^[^{]*', '', content)
            json_data = json.loads(content)
            return json_data

    def save_data_to_json(self, endpoint: str):
        data = self.pull_data(endpoint=endpoint)

        self._verify_endpoint(endpoint)

        output_path = self.mods_json_path if endpoint == 'mods' else self.bases_json_path

        with open(output_path, "w") as f:
            json.dump(data, f, indent=4)
