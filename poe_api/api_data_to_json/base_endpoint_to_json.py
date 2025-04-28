from abc import ABC, abstractmethod
import json
import logging
import os
import re
import requests

from utils import Config, StringProcessor


class BaseEndpointToJson(ABC):

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.api_url = (StringProcessor(string=Config.API_JSON_DATA_BASE_URL.value)
                        .attach_url_endpoint(endpoint=self.endpoint)
                        .string
                        )

        self.json_output_path = (StringProcessor(os.getcwd())
                                 .attach_file_path_endpoint(Config.JSON_FILE_PATH.value)
                                 .attach_file_path_endpoint(endpoint=f"/{self.endpoint}.json")
                                 .string
                                 )

        self.headers = {
            'Accept': 'image/avif,image/webp,image/png,image/svg+xml,image/*;q=0.8,*/*;q=0.5',
            'Referer': self.api_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
        }

    def _load_api_data(self):
        logging.info(f"Loading stat modifiers from PoE API at url {self.api_url}")
        response = requests.get(url=self.api_url,
                                headers=self.headers)
        response.raise_for_status()
        logging.info("\tSuccessfully loaded stat modifiers from PoE API.")

        json_data = response.json()
        return json_data

    @abstractmethod
    def _format_data(self, data: dict) -> dict:
        return data
    
    def _output_data_to_json(self, data: dict):
        with open(self.json_output_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def execute(self):
        data = self._load_api_data()
        data = self._format_data(data=data)
        self._output_data_to_json(data=data)
