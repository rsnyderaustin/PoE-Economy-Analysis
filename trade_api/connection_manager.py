
import requests

from utils import EnvLoader, EnvVar


class TradeConnectionManager:

    base_url = "https://www.pathofexile.com/api/trade2/"
    search_url = base_url + "search/poe2/Standard"
    fetch_url = base_url + "fetch/"

    header = {
        'content-type': 'application/json',
        'user-agent': '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'cookie': f'POESESSID={EnvLoader.get_env(env_variable=EnvVar.POSSESSID}}',
        'accept': '*/*',
        'connection': 'keep-alive'
    }

    @classmethod
    def _post_for_search_id(cls):

        

        response = requests.post(url=cls.search_url,
                                 headers=cls.header,
                                 json=query)

    def search(self):
        pass


