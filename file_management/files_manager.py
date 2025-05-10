import json
import logging
import os
from enum import Enum
from pathlib import Path

import pandas as pd
import xgboost as xgb

from instances_and_definitions import ItemMod, ModifiableListing
from . import utils


class FileKey(Enum):
    ATYPE_MODS = 'atype_mods'
    CURRENCY_CONVERSIONS = 'currency_conversions'
    LISTING_FETCHES = 'listing_fetches'
    CRITICAL_PRICE_PREDICT_TRAINING = 'price_predict_data'
    PRICE_PREDICT_MODEL = 'price_predict_model'
    MARKET_SCAN = 'temp_price_predict_data'


class FilesManager:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(FilesManager, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        self.file_paths = {
            FileKey.CURRENCY_CONVERSIONS: Path.cwd() / 'file_management/files/currency_prices.csv',
            FileKey.LISTING_FETCHES: Path.cwd() / 'file_management/files/listing_fetches.json',
            FileKey.CRITICAL_PRICE_PREDICT_TRAINING: Path.cwd() / 'file_management/files/listings.json',
            FileKey.PRICE_PREDICT_MODEL: Path.cwd() / 'file_management/files/price_predict_model.json',
            FileKey.MARKET_SCAN: Path.cwd() / 'file_management/files/market_scan.json'
        }

        self.file_data = dict()

        self._load_files()

    def _load_files(self):

        model = xgb.Booster()
        model_path = self.file_paths[FileKey.PRICE_PREDICT_MODEL]
        if os.path.getsize(model_path) > 2:
            model.load_model(self.file_paths[FileKey.PRICE_PREDICT_MODEL])
            self.file_data[FileKey.PRICE_PREDICT_MODEL] = model
        else:
            self.file_data[FileKey.PRICE_PREDICT_MODEL] = None

        file_paths = {file_key: path for file_key, path in self.file_paths.items() if file_key != FileKey.PRICE_PREDICT_MODEL}

        for key, path in file_paths.items():
            if path.exists:
                if path.suffix == '.json':
                    with open(path, 'r') as file:
                        self.file_data[key] = json.load(file)
                elif path.suffix == '.csv':
                    self.file_data[key] = pd.read_csv(path)

        self.file_data[FileKey.LISTING_FETCHES] = {
            date: set(listing_ids)
            for date, listing_ids in self.file_data[FileKey.LISTING_FETCHES].items()
        }

    def cache_mod(self, item_mod: ItemMod):
        mod_data = self.file_data[FileKey.ATYPE_MODS]
        if item_mod.atype not in mod_data:
            mod_data[item_mod.atype] = dict()

        atype_dict = mod_data[item_mod.atype]

        if item_mod.mod_id not in mod_data[item_mod.atype]:
            atype_dict[item_mod.mod_id] = {
                'mod_class': item_mod.mod_class.value,
                'sub_mod_ids': [sub_mod.mod_id for sub_mod in item_mod.sub_mods],
                'mod_types': item_mod.mod_types,
                'mod_texts': [sub_mod.sanitized_mod_text for sub_mod in item_mod.sub_mods],
                'affix_type': item_mod.affix_type.value if item_mod.affix_type else None, # Some mods don't have affix types
                'mod_tiers': dict()
            }

        mod_tiers_dict = atype_dict[item_mod.mod_id]['mod_tiers']

        if str(item_mod.mod_ilvl) not in mod_tiers_dict:
            mod_id_to_values_ranges = {
                sub_mod.mod_id: sub_mod.values_ranges
                for sub_mod in item_mod.sub_mods
            }
            mod_tiers_dict[item_mod.mod_ilvl] = {
                'ilvl': int(item_mod.mod_ilvl),
                'mod_id_to_values_ranges': mod_id_to_values_ranges,
                'weighting': item_mod.weighting
            }

    def cache_api_fetch_date(self, listing_ids, fetch_date: str):
        dates_fetched = self.file_data[FileKey.LISTING_FETCHES]
        if fetch_date not in dates_fetched:
            dates_fetched[fetch_date] = set()

        dates_fetched[fetch_date].update(listing_ids)

    def cache_training_data(self, training_data: dict):
        self.file_data[FileKey.CRITICAL_PRICE_PREDICT_TRAINING] = training_data

    def cache_price_prediction_model(self, price_predict_model):
        self.file_data[FileKey.PRICE_PREDICT_MODEL] = price_predict_model

    def save_data(self, keys: list[FileKey] = None):
        if keys:
            file_paths = {file_key: path for file_key, path in self.file_paths.items() if file_key in keys}
        else:
            file_paths = self.file_paths

        logging.info("Exporting data.")
        for key, file_path in file_paths.items():
            utils.write_to_file(data=self.file_data[key], file_path=file_path)



