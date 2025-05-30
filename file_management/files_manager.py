import json
import logging
import os
import pickle
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd
import xgboost as xgb
from stable_baselines3 import PPO

from shared.logging import log_errors


class DataPath(Enum):
    MODS = Path.cwd() / 'file_management/dynamic_files/item_mods.pkl'
    CURRENCY_CONVERSIONS = Path.cwd() / 'file_management/static_files/currency_prices.csv'
    POE2DB_MODS = Path.cwd() / 'file_management/static_files/poe2db_mods.pkl'
    OFFICIAL_STATIC = Path.cwd() / 'file_management/static_files/official_static.json'
    OFFICIAL_STATS = Path.cwd() / 'file_management/static_files/official_stats.json'
    RAW_LISTINGS = Path.cwd() / 'file_management/dynamic_files/raw_listings.json'
    GLOBAL_POECD_MANAGER = Path.cwd() / 'file_management/dynamic_files/global_poe2db_manager.pkl'


class ModelPath(Enum):
    PRICE_PREDICT_MODELS_DIRECTORY = Path.cwd() / 'file_management/price_predict_models'
    CRAFTING_MODELS_DIRECTORY = Path.cwd() / 'file_management/crafting_models'


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


class FilesManager:
    _instance = None
    _initialized = None

    def __new__(cls):
        if not getattr(cls, '_instance', None):
            cls._instance = super(FilesManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self._file_data = dict()

    @staticmethod
    def _create_file(path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=False)

    @log_errors(logging.getLogger())
    def fetch_data(self, data_path_e: DataPath, default: Any = None, missing_ok=True):
        if data_path_e in self._file_data:
            return self._file_data[data_path_e]

        path = data_path_e.value

        supported_types = {'.json', '.csv', '.pkl'}
        if path.suffix not in supported_types:
            raise ValueError(f"Unsupported file type {path.suffix}")

        if not path.exists():
            if not missing_ok:
                raise FileNotFoundError(f"File at path {str(path)} from enum {data_path_e} not found.")

            logging.info(f"Path '{str(path)}' does not exist. Creating with default {default}")
            self._create_file(path)

            # If the path doesn't exist then we write the default there and let the rest of the program load it as normal
            self._write_to_file(file_path=path, data=default)

        if path.suffix == '.json':
            with open(path, encoding='utf-8') as file:
                try:
                    data = json.load(file)
                except json.decoder.JSONDecodeError:
                    data = default
                self._file_data[data_path_e] = data
                return data
        elif path.suffix == '.csv':
            data = pd.read_csv(path)
            self._file_data[data_path_e] = data
            return data
        elif path.suffix == '.pkl':
            with open(path, 'rb') as file:
                data = pickle.load(file)

                if not data and not missing_ok:
                    raise RuntimeError(f"No data found for path {data_path_e} and missing_ok is False.")

                data = data if data else default  # If the pkl is empty then it returns None, but we want our default
                self._file_data[data_path_e] = data
                return data

    @staticmethod
    def _write_to_file(file_path: Path, data):
        if file_path.suffix not in {'.json', '.csv', '.pkl'}:
            raise ValueError(f"Unsupported file type {file_path.suffix}")

            # Write to a temp file in the same directory
        with tempfile.NamedTemporaryFile(mode='wb' if file_path.suffix == '.pkl' else 'w',
                                         dir=file_path.parent,
                                         delete=False,
                                         suffix=file_path.suffix,
                                         encoding='utf-8' if file_path.suffix in {'.json', '.csv'} else None) as tmp:
            tmp_path = Path(tmp.name)

            if file_path.suffix == '.json':
                json.dump(data, tmp, indent=2, cls=SetEncoder)
            elif file_path.suffix == '.csv':
                # pandas to_csv wants a file path or file-like object
                tmp.close()
                data.to_csv(tmp_path, index=False)
            elif file_path.suffix == '.pkl':
                pickle.dump(data, tmp)

            # Atomic move
        os.replace(tmp_path, file_path)

    def cache_data(self, data_path: DataPath, data: Any):
        self._file_data[data_path] = data

    def save_data(self, paths: list[DataPath]):
        for path_e in paths:
            path = path_e.value
            if not path.exists():
                self._create_file(path)

            if path_e not in self._file_data:
                raise ValueError(f"DataPath {path_e} has no data to save.")
            self._write_to_file(data=self._file_data[path_e],
                                file_path=path_e.value)

    @staticmethod
    def save_price_predict_model(atype: str, model: xgb.Booster):
        folder_path = ModelPath.PRICE_PREDICT_MODELS_DIRECTORY.value
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / f"{atype}.json"
        model.save_model(str(file_path))

    @staticmethod
    def load_price_predict_model(atype: str):
        folder_path = ModelPath.PRICE_PREDICT_MODELS_DIRECTORY.value
        model = xgb.Booster()
        file_path = folder_path / f"{atype}.json"

        if os.path.getsize(file_path) <= 2:
            return None

        return model.load_model(str(file_path))

    @staticmethod
    def save_crafting_model(atype: str, model: PPO):
        folder_path = ModelPath.CRAFTING_MODELS_DIRECTORY.value
        folder_path.mkdir(parents=True, exist_ok=True)

        file_path = folder_path / f"{atype}"
        model.save(file_path)

    @staticmethod
    def load_crafting_model(atype: str):
        folder_path = ModelPath.CRAFTING_MODELS_DIRECTORY.value
        file_path = folder_path / f"{atype}.zip"

        if not os.path.exists(file_path):
            return None

        return PPO.load(file_path)



