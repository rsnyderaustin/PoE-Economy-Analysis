
import json
import re
from enum import Enum

import requests

from shared import PathProcessor


class PoecdEndpoint(Enum):
    BASES = '/lang/poec_lang.us.json?v=1744834998'
    STATS = '/main/poec_data.json?v=1744834989'


class PoecdDataPuller:

    def __init__(self):

        # Input

        self.source_url = 'https://www.craftofexile.com/json/poe2/'

        self.bases_input_url = (
            PathProcessor(
                path=self.source_url
            )
            .attach_url_endpoint(endpoint=PoecdEndpoint.BASES.value)
            .path
        )

        self.mods_input_url = (
            PathProcessor(
                path=self.source_url
            )
            .attach_url_endpoint(endpoint=PoecdEndpoint.STATS.value)
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

    def pull_data(self, endpoint: PoecdEndpoint):

        import_url = self.mods_input_url if endpoint == PoecdEndpoint.STATS else self.bases_input_url
        response = requests.get(url=import_url,
                                headers=self.headers,
                                cookies=self.cookies)
        response.raise_for_status()

        content = response.content.decode('utf-8')
        content = re.sub(r'^[^{]*', '', content)
        json_data = json.loads(content)

        return json_data

