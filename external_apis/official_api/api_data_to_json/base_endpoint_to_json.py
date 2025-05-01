import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import requests

from utils import PathProcessor


class BaseEndpointToJson(ABC):

    def __init__(self,
                 official_data_source_base_url: str,
                 json_output_path: Path,
                 endpoint: str):
        self.endpoint = endpoint
        self.api_url = (PathProcessor(string=official_data_source_base_url)
                        .attach_url_endpoint(endpoint=self.endpoint)
                        .string
                        )

        self.json_output_path = json_output_path

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
        with self.json_output_path.open('w') as json_file:
            json.dump(data, json_file, indent=4)

    def execute(self) -> dict:
        data = self._load_api_data()
        data = self._format_data(data=data)
        self._output_data_to_json(data=data)
        return data
