
import json
import logging
import os
from pathlib import Path

from .api_data_to_json import StatDataToJsonHandler, StaticDataToJsonHandler
from .official_enums import OfficialConfig


class OfficialDataPuller:

    stats_endpoint = 'external_apis/official_api/json_data/stats.json'
    static_endpoint = 'external_apis/official_api/json_data/static.json'

    stats_json_path = Path.cwd() / stats_endpoint
    static_json_path = Path.cwd() / static_endpoint

    @classmethod
    def pull_static_data(cls, reload_data: bool = True):
        if not cls.static_json_path.exists() or reload_data:
            static_to_json = StaticDataToJsonHandler(
                official_data_source_base_url=OfficialConfig.API_JSON_DATA_BASE_URL.value,
                json_output_path=cls.static_json_path
            )
            static_to_json.execute()

        with cls.static_json_path.open('r', encoding='utf-8') as static_file:
            return json.load(static_file)

    @classmethod
    def pull_stats_data(cls, reload_data: bool = True):
        if not cls.stats_json_path.exists() or reload_data:
            stats_to_json = StatDataToJsonHandler(
                official_data_source_base_url=OfficialConfig.API_JSON_DATA_BASE_URL.value,
                json_output_path=cls.stats_json_path
            )
            data = stats_to_json.execute()

        with cls.stats_json_path.open('r', encoding='utf-8') as static_file:
            return json.load(static_file)
