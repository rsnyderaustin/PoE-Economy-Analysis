
import json
import re
import requests

from utils import StringProcessor
from .enums import Endpoint, Url


class CraftOfExileDataPuller:
    cookies = {
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

    headers = {
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

    params = {
        'v': '1744834989',
    }

    @classmethod
    def pull_data(cls, endpoint: Endpoint):
        api_url = (StringProcessor(string=Url.BASE_URL.value)
                   .attach_url_endpoint(endpoint=endpoint.value)
                   .string)
        response = requests.get(
            api_url,
            headers=cls.headers,
            cookies=cls.cookies,
            params=cls.params
        )

        content = response.content.decode('utf-8')
        content = re.sub(r'^[^{]*', '', content)
        json_data = json.loads(content)
        return json_data

