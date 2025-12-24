
import json
import logging
from uuid import uuid4

from PIL import Image

from currency_analysis.ui_capture import CurrencyExchangeUiElement, ScreenShotCollection

logger = logging.getLogger(__name__)
import os
from enum import Enum
from pathlib import Path

class CacheObject(Enum):
    MARKET_DATA_MANAGER = 'market_data_manager'
    SCREEN_SHOT_COLLECTION = 'screen_shot_collection'


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
    _cache_root = Path(__file__).parent / 'cache'

    @classmethod
    def get_cache_dir(cls, cache_object: CacheObject) -> Path:
        path = cls._cache_root / cache_object.value
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def load_json(cls, path: Path) -> dict | None:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def save_json(cls, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


class MarketDataImageCache:

    def __init__(self):
        self._root = CacheManager.get_cache_dir(CacheObject.MARKET_DATA_MANAGER)

    def save(self, screen_shot_collection: ScreenShotCollection):
        collection_dir = self._root / screen_shot_collection.id_
        collection_dir.mkdir(parents=True, exist_ok=True)

        for ui_element, screen_shots in screen_shot_collection.screen_shots().items():
            images_dir = collection_dir / ui_element.value
            images_dir.mkdir(parents=True, exist_ok=True)
            for i, screen_shot in enumerate(screen_shots):
                image_path = images_dir / f"{i}.png"
                image = Image.from_array(screen_shot.ndarray)
                image.save(image_path)

            CacheManager.save_json(images_dir, {'ui_element': ui_element.value})

    def load_metadata(self, image_id: str) -> dict | None:
        return CacheManager.load_json(
            self._root / image_id / "metadata.json"
        )

    def list_records(self) -> list[str]:
        return [
            p.name for p in self._root.iterdir()
            if p.is_dir()
        ]




