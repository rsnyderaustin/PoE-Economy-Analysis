import json
import logging
import os
import pickle
import shutil
from enum import Enum
from pathlib import Path

import pandas as pd
import xgboost as xgb


class DataPath(Enum):
    MODS = Path.cwd() / 'file_management/files/item_mods.pkl'
    CURRENCY_CONVERSIONS = Path.cwd() / 'file_management/files/currency_prices.csv'
    MARKET_SCAN = Path.cwd() / 'file_management/files/market_scan.json'
    POECD_BASES = Path.cwd() / 'file_management/files/poecd_bases.json'
    POECD_STATS = Path.cwd() / 'file_management/files/poecd_stats.json'
    OFFICIAL_STATIC = Path.cwd() / 'file_management/files/official_static.json'
    OFFICIAL_STATS = Path.cwd() / 'file_management/files/official_stats.json'
    MOD_ENCODES = Path.cwd() / 'file_management/files/mod_encodes.json'
    RAW_LISTINGS = Path.cwd() / 'file_management/files/raw_listings.json'


class ModelPath(Enum):
    PRICE_PREDICT_MODEL = Path.cwd() / 'file_management/files/price_predict_ai_model.json'
    CRAFTING_MODEL = Path.cwd() / 'file_management/files/crafting_ai_model.pt'


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


def _write_json(data, file_path):
    if isinstance(data, xgb.Booster):
        data.save_model(file_path)
    else:
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        with open(tmp_path, 'w') as training_data_json_path:
            json.dump(data, training_data_json_path, indent=4, cls=SetEncoder)
            training_data_json_path.flush()
            os.fsync(training_data_json_path.fileno())

        # Manual copy and remove
        shutil.copyfile(tmp_path, file_path)
        os.remove(tmp_path)


def write_to_file(file_path: Path, data):
    if file_path.suffix == '.json':
        _write_json(data=data, file_path=file_path)
    elif file_path.suffix == '.csv':
        data.to_csv(file_path)
    elif file_path.suffix == '.pkl':
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
    else:
        raise ValueError(f"Unsupported file type {file_path.suffix}")


def _ensure_brackets_in_json(file_path: Path):
    if file_path.read_text().strip() == "":
        with open(file_path, 'w') as f:
            json.dump({}, f, indent=4)


def load_data_files() -> dict:
    file_data = dict()

    # Handle everything except the price predict model load now
    file_paths = {data_path_e: data_path_e.value for data_path_e in DataPath}

    for key, path in file_paths.items():
        if path.exists:
            if path.suffix == '.json':
                _ensure_brackets_in_json(file_path=path)
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
    file_data[DataPath .LISTING_FETCH_DATES] = {
        fetch_date: set(listing_ids)
        for fetch_date, listing_ids in file_data[DataPath.LISTING_FETCH_DATES].items()
    }

    return file_data


def _load_xgboost_model(model_enum):
    model = xgb.Booster()
    model_path = str(ModelPath[model_enum])

    if os.path.getsize(model_path) > 2:
        model.load_model(model_path)
        return model
    else:
        return None


def _load_crafting_model(model_enum):
    model = 0
    return model


def load_models() -> dict:
    model_data = dict()
    model_paths = {model_path_e: model_path_e.value for model_path_e in ModelPath}
    for model_path_e, model_path in model_paths.items():
        if model_path.suffix == '.json':
            model_data[model_path_e] = _load_xgboost_model(model_path_e)
        else:  # Not sure how we're storing crafting model yet, but we know it's not JSON
            model_data[model_path_e] = _load_crafting_model(model_path_e)
    return model_data

