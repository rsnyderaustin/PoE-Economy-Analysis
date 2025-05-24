from shared import ModClass


class ApiResponseParser:

    def __init__(self, api_response_data: dict):
        self.api_d = api_response_data

    def fetch_mods_data(self, mod_class: ModClass = None, mod_class_abbrev: str = None):
        


