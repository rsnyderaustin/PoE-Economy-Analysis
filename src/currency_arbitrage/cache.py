
import json
import logging
from uuid import uuid4

import cv2
from PIL import Image

from src.currency_arbitrage.data_management import MarketDataManager, GoldCostManager
from src.currency_arbitrage.data_objects import Currency
from src.currency_arbitrage.ui_capture import UiElement, MarketImageCollection

logger = logging.getLogger(__name__)
from enum import Enum
from pathlib import Path

class CacheObject(Enum):
    MARKET_DATA_MANAGER = 'market_data_manager'
    IMAGE_COLLECTIONS_MANAGER = 'image_collections_manager'
    GOLD_COST_MANAGER = 'gold_cost_manager'


class CacheSettings:

    def __init__(self):
        self._settings = dict()

    def add_settings(self,
                     cache_objects: list[CacheObject],
                     load_from_cache: bool,
                     save_to_cache: bool,
                     missing_ok: bool):
        for cache_object in cache_objects:
            self._settings[cache_object] = {'load': load_from_cache, 'save': save_to_cache, 'missing_ok': missing_ok}

    def should_load_from_cache(self, cache_object: CacheObject) -> bool:
        return self._settings[cache_object]['load']

    def should_save_to_cache(self, cache_object: CacheObject) -> bool:
        return self._settings[cache_object]['save']

    def missing_ok(self, cache_object: CacheObject) -> bool:
        return self._settings[cache_object]['missing_ok']


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
    def save_json(cls, data: dict, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


class MarketDataImagesCache:

    def __init__(self):
        self._root = CacheManager.get_cache_dir(CacheObject.IMAGE_COLLECTIONS_MANAGER)

    def save(self, image_collection: MarketImageCollection):
        raise NotImplementedError
        collection_dir = self._root / image_collection.id_
        collection_dir.mkdir(parents=True, exist_ok=True)
        
        c = image_collection
        if isinstance(c, MarketImageCollection):
            metadata = {
                'type': 'market_data',
                'have_currency': c.have_currency,
                'want_currency': c.want_currency,
                'collection_id': c.id_,
                'date_taken': c.date_taken.isoformat(),
                'available_currency_images':(
                    [i.to_dict() for i in c.available_currency_images]
                     if c.available_currency_images else []
                )
                ,
                'competing_currency_images': (
                    [i.to_dict() for i in c.competing_currency_images]
                    if c.competing_currency_images else []
                )
            }
        else:
            raise NotImplementedError

        metadata = {
            'have_currency': image_collection.have_currency.value,
            'want_currency': image_collection.want_currency.value,
            'collection_id': str(uuid4()),
            'date_taken': image_collection.date_taken.isoformat(),
            'stored_ui_elements': [e.value for e in image_collection.stored_ui_elements],
            'ui_element_image_ids': dict()
        }
        for ui_element, images in image_collection.images_d.items():
            metadata['ui_element_image_ids'][ui_element.value] = list()
            for image in images:
                png_path = collection_dir / f"{image.id_}.png"
                png = Image.fromarray(image.img_array)
                png.save(png_path)

                metadata['ui_element_image_ids'][ui_element.value].append(image.id_)

        CacheManager.save_json(path=collection_dir / 'metadata.json',
                               data=metadata)

    def load(self, missing_ok: bool) -> list[MarketImageCollection]:
        collections = []
        for subdir in self._root.iterdir():
            if not subdir.is_dir():
                continue

            metadata = CacheManager.load_json(path=subdir / 'metadata.json')

            collection = ImageCollection(have_currency=Currency(metadata['have_currency']),
                                         want_currency=Currency(metadata['want_currency']),
                                         date_taken=metadata['date_taken'])

            for ui_enum_str, ui_element_ids in metadata['ui_element_image_ids'].items():
                ui_element = UiElement(ui_enum_str)
                images = [
                    cv2.imread(str(subdir / f"{image_id}.png"), cv2.IMREAD_UNCHANGED)
                    for image_id in ui_element_ids
                ]
                collection.add_images(ui_element=ui_element,
                                      images=images)

            collections.append(collection)

        if not missing_ok and not collections:
            raise ValueError(f"No UiImageCollections loaded and missing_ok is False")

        return collections


class MarketDataManagerCache:

    def __init__(self):
        self._path = CacheManager.get_cache_dir(CacheObject.MARKET_DATA_MANAGER) / 'data.json'

    def save(self, manager: MarketDataManager):
        logger.info("Saving MarketDataManager to cache...")
        d = manager.to_dict()
        CacheManager.save_json(data=d, path=self._path)
        logger.info("\tFinished saving to cache")

    def load(self, missing_ok: bool) -> MarketDataManager | None:
        logger.info("Loading MarketDataManager from cache...")
        d = CacheManager.load_json(path=self._path)

        if not d:
            if not missing_ok:
                raise ValueError(f"No MarketDataManager data loaded when missing_ok is False")

            logger.info("\tNo cache data found. Returning None...")
            return None

        manager = MarketDataManager.from_dict(d)
        logger.info("\tFinished loading from cache")
        return manager


class GoldCostManagerCache:

    def __init__(self):
        self._path = CacheManager.get_cache_dir(CacheObject.GOLD_COST_MANAGER) / 'data.json'

    def save(self, gold_cost_manager: GoldCostManager):
        logger.info("Saving GoldCostManager to cache...")
        d = gold_cost_manager.to_dict()
        CacheManager.save_json(data=d, path=self._path)
        logger.info("\tFinished saving to cache")

    def load(self, missing_ok: bool) -> GoldCostManager | None:
        logger.info("Loading GoldCostManager from cache...")
        d = CacheManager.load_json(path=self._path)

        if not d:
            if not missing_ok:
                raise ValueError(f"No GoldCostManager data loaded when missing_ok is False")

            logger.info("\tNo cache data found. Returning None...")
            return None

        manager = GoldCostManager.from_dict(d)
        logger.info("\tFinished loading from cache")
        return manager

