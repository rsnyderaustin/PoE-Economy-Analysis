from .base_endpoint_to_json import BaseEndpointToJson


class StaticDataToJsonHandler(BaseEndpointToJson):

    def __init__(self,
                 official_data_source_base_url: str,
                 json_output_path: str,):
        super().__init__(official_data_source_base_url=official_data_source_base_url,
                         json_output_path=json_output_path,
                         endpoint='/static')

    def _format_data(self, data: dict):

        item_blocks = data['result']

        returnable_dict = dict()
        for item_block in item_blocks:
            item_block_name = item_block['id'].lower()
            returnable_dict[item_block_name] = list()

            for entry in item_block['entries']:
                if (not entry['id'] or len(entry['id']) == 0
                        or not entry['text'] or len(entry['text']) == 0):
                    continue

                if 'image' in entry:
                    del entry['image']

                returnable_dict[item_block_name].append(entry)

        return returnable_dict
