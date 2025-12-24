
import json
import logging
logger = logging.getLogger(__name__)
import os
from enum import Enum
from pathlib import Path


class CacheObject(Enum):
    MARKET_DATA_MANAGER = 'market_data_manager'


class CacheSettings:

    def __init__(self):
        self._settings = dict()

    def add_settings(self,
                     cache_objects: list[CacheObject],
                     load_from_cache: bool,
                     save_to_cache: bool):
        for cache_object in cache_objects:
            self._settings[cache_object] = {'load': load_from_cache, 'save': save_to_cache}

    def should_load_from_cache(self, cache_object: CacheObject) -> bool:
        return self._settings[cache_object]['load']

    def should_save_to_cache(self, cache_object: CacheObject) -> bool:
        return self._settings[cache_object]['save']


class CacheManager:

    _cache_path = Path(__file__).parent / 'cache.json'

    @classmethod
    def _ensure_cache_file(cls):
        cls._cache_path.parent.mkdir(parents=True, exist_ok=True)
        if not cls._cache_path.exists():
            cls._cache_path.write_text('{}')

    @classmethod
    def load_from_cache(cls, cache_object: CacheObject):
        cls._ensure_cache_file()

        with cls._cache_path.open('r') as f:
            cache = json.load(f)

        json_data = cache.get(cache_object.value)
        if json_data is None:
            logger.info(f"Unable to load {cache_object.value} from cache. Returning None...")
        return json_data

    @classmethod
    def save_to_cache(cls, d: dict, cache_object: CacheObject):
        cls._ensure_cache_file()

        with cls._cache_path.open('r') as f:
            cache = json.load(f)

        cache[cache_object.value] = d

        with cls._cache_path.open('w') as f:
            json.dump(cache, f, indent=2)

