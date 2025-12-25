
import json
import logging
from uuid import uuid4

from PIL import Image

from currency_analysis.ui_capture import CurrencyExchangeUiElement, UiImageCollection

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

    def save(self, image_collection: UiImageCollection):
        collection_dir = self._root / image_collection.id_
        collection_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            'collection_id': str(uuid4()),
            'date_taken': image_collection.date_taken,
            'stored_ui_elements': image_collection.stored_ui_elements,
        }
        for ui_element, images in image_collection.images_d.items():
            metadata[ui_element.value] = list()
            for image in images:
                image_path = collection_dir / f"{image.id_}.png"
                image = Image.fromarray(image.ndarray)
                image.save(image_path)

                metadata[ui_element.value].append(screen_shot.id_)

        CacheManager.save_json(path=collection_dir / 'metadata.json',
                               data=metadata)

    def load(self) -> list[UiImageCollection]:
        collections = []
        for subdir in self._root.iterdir():
            if not subdir.is_dir():
                continue

            metadata = CacheManager.load_json(path=subdir / 'metadata.json')

            collection = UiImageCollection(date_taken=metadata['date_taken'])

            ui_enum_strings = {e.value for e in CurrencyExchangeUiElement}
            for k, v in metadata.items():
                if k not in ui_enum_strings:
                    continue

                ui_element = CurrencyExchangeUiElement(k)
                images = [
                    cv2.imread(str(subdir / f"{image_id}.png"), cv2.IMREAD_UNCHANGED)
                    for image_id in v
                ]
                collection.add_images(ui_element=ui_element,
                                      images=images)

            collections.append(collection)

        return collections


    def load_metadata(self, image_id: str) -> dict | None:
        return CacheManager.load_json(
            self._root / image_id / "metadata.json"
        )

    def list_records(self) -> list[str]:
        return [
            p.name for p in self._root.iterdir()
            if p.is_dir()
        ]




