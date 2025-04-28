
import json
import logging
from pathlib import Path

from .api_data_to_json import StatDataToJsonHandler, StaticDataToJsonHandler
from .official_enums import OfficialConfig


class OfficialDataPuller:

    stats_json_path = Path(
        'C:/Users/austisnyder/Documents/GitHub/PoE-Economy-Analysis/external_apis/official_api/json_data/stats.json'
    )
    static_json_path = Path(
        'C:/Users/austisnyder/Documents/GitHub/PoE-Economy-Analysis/external_apis/official_api/json_data/static.json'
    )

    @classmethod
    def pull_static_data(cls, reload_data: bool = True):
        if not cls.static_json_path.exists() or reload_data:
            logging.error(f"Could not find Official static JSON path:\n\t{cls.static_json_path}. Attempting to create.")
            static_to_json = StaticDataToJsonHandler(
                official_data_source_base_url=OfficialConfig.API_JSON_DATA_BASE_URL.value,
                json_output_path=OfficialConfig.JSON_FILE_PATH.value
            )
            static_to_json.execute()

        with cls.static_json_path.open('r', encoding='utf-8') as static_file:
            return json.load(static_file)

    @classmethod
    def pull_stats_data(cls, reload_data: bool = True):
        if not cls.stats_json_path.exists() or reload_data:
            stats_to_json = StatDataToJsonHandler(
                official_data_source_base_url=OfficialConfig.API_JSON_DATA_BASE_URL.value,
                json_output_path=OfficialConfig.JSON_FILE_PATH.value
            )
            stats_to_json.execute()

        with cls.static_json_path.open('r', encoding='utf-8') as static_file:
            return json.load(static_file)
