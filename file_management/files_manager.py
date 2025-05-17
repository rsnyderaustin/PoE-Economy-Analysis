import json
import logging
import os
import pickle
from enum import Enum
from pathlib import Path

import pandas as pd
import xgboost as xgb

from . import utils


class FileKey(Enum):
    MODS = 'mods'
    CURRENCY_CONVERSIONS = 'currency_conversions'
    LISTING_FETCHES = 'listing_fetches'
    CRITICAL_PRICE_PREDICT_TRAINING = 'price_predict_data'
    PRICE_PREDICT_MODEL = 'price_predict_model'
    MARKET_SCAN = 'temp_price_predict_data'
    POECD_BASES = 'poecd_bases'
    POECD_STATS = 'poecd_stats'


class FilesManager:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(FilesManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self.file_paths = {
            FileKey.MODS: Path.cwd() / 'file_management/files/item_mods.pkl',
            FileKey.CURRENCY_CONVERSIONS: Path.cwd() / 'file_management/files/currency_prices.csv',
            FileKey.LISTING_FETCHES: Path.cwd() / 'file_management/files/listing_fetch_dates.json',
            FileKey.MARKET_SCAN: Path.cwd() / 'file_management/files/market_scan.json',
            FileKey.POECD_BASES: Path.cwd() / 'file_management/files/poecd_bases.json',
            FileKey.POECD_STATS: Path.cwd() / 'file_management/files/poecd_stats.json'
        }

        self.model_paths = {
            FileKey.PRICE_PREDICT_MODEL: Path.cwd() / 'file_management/files/price_predict_model.json'
        }

        self.file_data = self._load_files()
        self.model_data = self._load_models()

        self._initialized = True

    def _ensure_brackets_in_json(self, file_path: Path):
        if file_path.read_text().strip() == "":
            with open(file_path, 'w') as f:
                json.dump({}, f, indent=4)

    def _load_files(self) -> dict:
        file_data = dict()

        # Handle everything except the price predict model load now
        file_paths = {file_key: path for file_key, path in self.file_paths.items() if file_key != FileKey.PRICE_PREDICT_MODEL}

        for key, path in file_paths.items():
            if path.exists:
                if path.suffix == '.json':
                    self._ensure_brackets_in_json(file_path=path)
                    with open(path, 'r') as file:
                        file_data[key] = json.load(file)
                elif path.suffix == '.csv':
                    file_data[key] = pd.read_csv(path)
                elif path.suffix == '.pkl':
                    try:
                        with open(path, 'rb') as file:
                            file_data[key] = pickle.load(file)
                    except EOFError:
                        file_data[key] = None
                        logging.info(f"No data found at path {path}. Continuing.")
                        continue
                else:
                    raise ValueError(f"Unsupported file type {path.suffix}")

        # LISTING_FETCHES is a special case because its dict values are sets
        file_data[FileKey.LISTING_FETCHES] = {
            fetch_date: set(listing_ids)
            for fetch_date, listing_ids in file_data[FileKey.LISTING_FETCHES].items()
        }

        return file_data

    def _load_models(self) -> dict:
        model_data = dict()
        # Handle the price predict model load
        model = xgb.Booster()
        model_path = self.model_paths[FileKey.PRICE_PREDICT_MODEL]
        if os.path.getsize(model_path) > 2:
            model.load_model(self.model_paths[FileKey.PRICE_PREDICT_MODEL])
            model_data[FileKey.PRICE_PREDICT_MODEL] = model
        else:
            model_data[FileKey.PRICE_PREDICT_MODEL] = None

        return model_data

    def has_data(self, key: FileKey):
        file_path = self.file_paths[key]
        file_size = os.path.getsize(file_path)

        if file_path.suffix == '.json':
            return file_size >= 2
        else:
            return file_size > 0

    def save_data(self, keys: list[FileKey] = None):
        if keys:
            file_paths = {file_key: path for file_key, path in self.file_paths.items() if file_key in keys}
        else:
            file_paths = self.file_paths

        for key, file_path in file_paths.items():
            utils.write_to_file(data=self.file_data[key], file_path=file_path)

    def save_model(self, model_key: FileKey):
        logging.info(f"Exporting model {model_key}")
        utils.write_to_file(data=self.model_data[model_key], file_path=self.model_paths[model_key])



