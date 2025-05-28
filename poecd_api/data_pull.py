
import zstandard
import json
import re
from enum import Enum
from pathlib import Path
from urllib.parse import urljoin

import requests


def _normalize_data(bases_data: dict):
    bases_data['base'] = {
        k: ('Quarterstaff' if v == 'Warstaff' else v)
        for k, v in bases_data['base'].items()
    }


def _clean_cookie(cookie_str):
    return cookie_str.encode('latin-1', errors='ignore').decode('latin-1')


class PoecdEndpoint(Enum):
    BASES = '/lang/poec_lang.us.json?v=1744834998'
    STATS = '/main/poec_data.json?v=1744834989'


class PoecdDataPuller:

    def __init__(self):

        # Input

        self.source_url = 'https://www.craftofexile.com/json/poe2/'

        self.bases_input_url = urljoin(self.source_url, PoecdEndpoint.BASES.value)
        self.mods_input_url = urljoin(self.source_url, PoecdEndpoint.STATS.value)

        self.cookies = {
            'PHPSESSID': 'dbd4ba78e343f1a4f000e453093fe052',
            'cf_clearance': '4ZEbubyO3CWWIZnB3CfuBIuzPX1KqVLbdh8prZf9duI-1748459952-1.2.1.1-DNMZtyOYu6oIixYpTUzZnqhXmHRyL_pwLQDDTFERobF0N5YaGqh8b85Cdk7gVjecJNLOvwmMckPRG1WrF0cpXrMC7iTncjyL1BGCOZumrR.L3WJoZk8u70pNDNodJXZvrwP26QuaeFONzw1NWUq9bR4nuYWCzQ46qwGQAdAJLwM7mFlEDYu89w8GALqH7RYVyvitmb_QXLvlo0DszLoOe9upLMrzQceeVzVEBHniwA3QKcwVmalo7zwvWbMSAQhutkbmO3ENC7WNRWsoqSvdB_ssQZilBuYIPDV_D74ddvr4bw61sB0tjgyUCNPcTYN1neptZwD_Ps4RbPC7SsH7E8hKUyih44cPBeRCWyPXXxzd95kTlCHhivZNHQyDhy2z',
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
            "Host": "www.craftofexile.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Alt-Used": "www.craftofexile.com",
            "Connection": "keep-alive",
            "Referer": "https://www.craftofexile.com/?b=27&ob=both&v=d&a=x&l=a&lg=17&bp=y&as=1&hb=0&bld={}&im={}&ggt=|&ccp={}&gvc={%22limit%22:88}",
            "Cookie": "_ga_LP84H6PC5N=GS2.1.s1748462253$o18$g1$t1748463778$j60$l0$h0; _ga=GA1.1.1372265460.1745854670; _lr_env_src_ats=false; ncmp.domain=craftofexile.com; nitro-uid=%7B%22TDID%22%3A%22bbaa107a-110a-49eb-a42d-e648686c4fb7%22%2C%22TDID_LOOKUP%22%3A%22FALSE%22%2C%22TDID_CREATED_AT%22%3A%222025-05-28T19%3A58%3A52%22%7D; nitro-uid_cst=VyxHLMwsHQ%3D%3D; cto_bundle=t_Rvf19vdTdKMHZNZEYlMkJ6QiUyQktQSGF5a1N2em84Y2xSdlo1dTdzcTZPamREUTUyaHB4OW5NT3FaaEJaNFkzVmxieUtRVUZaYWtJRjRHd3ZvY3FDOCUyQkY5byUyRkZncEVQOHlBeUpKZzZjJTJCRHlMY1YwSCUyRjVRc3diT1BRRkZlQkRsRHk4VzRsQ2t4OGklMkJTMUJkTUxlV1UlMkJIR3VlU3dRJTNEJTNE; cto_bidid=iedQX19jJTJCTEdtWFEzcTJGUGM5MXVzR2dEM3RjUUN0Rkxveld1WHd3OXBkTTBpaVAzUU1XJTJCVkhCSkY1bk1SUm80cE5jT1BIQXBIVU90ZDF1SVF0azFnR29oUUo5VGUwM0dnMGhxaXFNQ2FSJTJGYjcwSTc0S1VjNEI2bDUycFhhWVFXdGpkeg; _cc_id=b021e3be43df9cccf1836b03ea3cc05a; 33acrossIdTp=%2F24TATwU2pKpKLWIrHs7KcHXMWQmZAU8bOREuBWs6AY%3D; _au_1d=AU1D-0100-001745854671-CC7PIUBC-CD2W; __gads=ID=b1363458456f65f1:T=1745854673:RT=1748462254:S=ALNI_Mb6u3MRGh1O2QKf-sTz5edU0UsfXA; __gpi=UID=000010a331738bbe:T=1745854673:RT=1748462254:S=ALNI_MYqoPi0n8aSdBz_AEnc2RSU4UBfBA; __eoi=ID=8167c89b572f35de:T=1745854673:RT=1748462254:S=AA-AfjYqeM0GW2jCJcjTPl77lgwt; _ga_FVWZ0RM4DH=GS2.1.s1748462279$o16$g1$t1748463778$j60$l0$h0; cto_dna_bundle=N6N2E195OCUyQlllb1dZOFBjbE50MTVkbVpqRThHMlZHbWJNJTJGQUNpbDVtVXpCSWF0eUZQMzFoSDN2OWJvSVNsRkF4VjNSMVgzTGRBQWI1bEhlWDNzekd6U2duTnclM0QlM0Q; PHPSESSID=m2i9v5f6b0r6gvia92f898kkjd; hbmd=0; _lr_retry_request=true; _iiq_fdata=%7B%22pcid%22%3A%22defe3071-e14b-fd1a-2397-55b575c34a08%22%2C%22pcidDate%22%3A1745854670767%2C%22gpc%22%3Afalse%2C%22sCal%22%3A1748462253733%2C%22isOptedOut%22%3Afalse%2C%22dbsaved%22%3A%22true%22%7D; panoramaId_expiry=1749067053792; panoramaId=ef48ad876831a26bf326b017341816d539386d180a516a513c0dd7d1fe2639d0; _lr_geo_location_state=IA; _lr_geo_location=US; _lr_sampling_rate=100; league=17; vmode=d; amode=x; blkprc=y; tagrps=true; tafilts=true; asmt=1; clng=us",
            "Sec-Fetch-Dest": "script",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "same-origin",
            "Priority": "u=2",
            "TE": "trailers"
        }

    def pull_data(self, endpoint: PoecdEndpoint):
        self.headers['Cookie'] = _clean_cookie(self.headers['Cookie'])
        self.cookies['cf_clearance'] = _clean_cookie(self.cookies['cf_clearance'])
        import_url = self.mods_input_url if endpoint == PoecdEndpoint.STATS else self.bases_input_url
        response = requests.get(url=import_url,
                                headers=self.headers,
                                cookies=self.cookies)
        response.raise_for_status()

        dc = zstandard.ZstdDecompressor()
        content = dc.decompress(response.content)
        content = response.content.decode('utf-8')
        content = re.sub(r'^[^{]*', '', content)
        json_data = json.loads(content)

        if endpoint == PoecdEndpoint.BASES:
            _normalize_data(json_data)

        return json_data

