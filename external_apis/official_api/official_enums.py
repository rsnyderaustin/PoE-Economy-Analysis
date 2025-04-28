
from enum import Enum


class OfficialConfig(Enum):
    QUERY_WAIT_TIME = 0.5
    API_JSON_DATA_BASE_URL = 'https://www.pathofexile.com/api/trade2/data/'
    JSON_FILE_PATH = '/external_apis/official_api/json_data/'
