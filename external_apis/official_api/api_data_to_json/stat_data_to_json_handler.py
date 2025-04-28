from pathlib import Path

from .base_endpoint_to_json import BaseEndpointToJson


class StatDataToJsonHandler(BaseEndpointToJson):

    def __init__(self,
                 official_data_source_base_url: str,
                 json_output_path: Path):
        super().__init__(official_data_source_base_url=official_data_source_base_url,
                         json_output_path=json_output_path,
                         endpoint='/stats')

    def _format_data(self, data: dict):
        stat_blocks = data['result']

        stat_json = {
            stat_block['id']: stat_block['entries'] for stat_block in stat_blocks
        }

        return stat_json






