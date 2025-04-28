

from .base_endpoint_to_json import BaseEndpointToJson


class StatModifiersToJson(BaseEndpointToJson):

    def __init__(self):
        super().__init__(endpoint='/stats')

    def _format_data(self, data: dict):
        stat_blocks = data['result']

        stat_json = {
            stat_block['id']: stat_block['entries'] for stat_block in stat_blocks
        }

        return stat_json






