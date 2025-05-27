import json
import logging
import os
import pickle
import shutil
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

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
    RAW_LISTINGS = Path.cwd() / 'file_management/files/raw_listings.json'
    GLOBAL_POECD_MANAGER = Path.cwd() / 'file_management/files/global_poecd_manager.pkl'


class ModelPath(Enum):
    PRICE_PREDICT_MODELS_DIRECTORY = Path.cwd() / 'file_management/price_predict_models'
    CRAFTING_MODELS_DIRECTORY = Path.cwd() / 'file_management/crafting_models'


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)
