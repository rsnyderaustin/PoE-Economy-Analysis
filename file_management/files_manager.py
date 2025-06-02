import json
import logging
import os
import tempfile
from abc import ABC
from pathlib import Path
from typing import Any

from instances_and_definitions import ItemMod
from poe2db_scrape.mods_management import Poe2DbModsManager
from shared.enums.item_enums import AType
from . import i_o_utils
from shared.logging import log_errors


class RawListingsFile:

    def __init__(self, path: Path = None):
        self._path = path or Path.cwd() / 'file_management/dynamic_files/raw_listings.json'

    def save(self, new_records: list[dict]):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, 'a', encoding='utf-8') as f:
            for record in new_records:
                json.dump(record, f)
                f.write('\n')

    def load(self, limit=20) -> 'Generator[dict[str, Any], None, None]':
        with open(self._path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                yield json.loads(line)


class _JsonDictFile(ABC):

    def __init__(self, path: Path = None):
        self._path = path

    def save(self, data: dict):
        i_o_utils.write_json(path=self._path, data=data)

    def load(self, default: Any = None) -> dict:
        return i_o_utils.load_json(path=self._path, default=default)


class OfficialStatsFile(_JsonDictFile):

    def __init__(self, path: Path = None):
        super().__init__(path or Path.cwd() / 'file_management/static_files/official_static.json')


class OfficialStaticFile(_JsonDictFile):

    def __init__(self, path: Path = None):
        super().__init__(path or Path.cwd() / 'file_management/static_files/official_static.json')


class CurrencyConversionsFile:

    def __init__(self, path: Path = None):
        self._path = path or Path.cwd() / 'file_management/static_files/currency_prices.csv'

    def load(self) -> 'pd.DataFrame':
        import pandas as pd

        return pd.read_csv(str(self._path))


class PickleFile(ABC):

    def __init__(self, path: Path = None):
        self._path = path or Path.cwd() / 'file_management/dynamic_files/item_mods.pkl'

        self._data = None

    def save(self, data):
        import pickle

        with tempfile.NamedTemporaryFile(mode='wb',
                                         dir=self._path.parent,
                                         delete=False,
                                         suffix=self._path.suffix) as tmp:
            tmp_path = Path(tmp.name)

            pickle.dump(data, tmp)

            # Atomic move
        os.replace(tmp_path, self._path)

    def load(self, default: Any = None, missing_ok: bool = True):
        import pickle

        if self._data:
            return self._data

        with open(self._path, 'rb') as file:
            data = pickle.load(file)

            if not missing_ok and not data:
                raise ValueError(f"missing_ok is False when there is no data for class {self.__class__.__name__}")

            data = data if data else default  # If the pkl is empty then it returns None, but we want our default

        self._data = data
        return data


class ItemModsFile(PickleFile):

    def __init__(self, path: Path = None):
        super().__init__(path)

    def load(self, default: Any = None, missing_ok: bool = True) -> dict:
        pass


class Poe2DbModsManagerFile(PickleFile):

    def __init__(self, path: Path = None):
        super().__init__(path)

    def load(self, default: Any = None, missing_ok: bool = True) -> Poe2DbModsManager:
        pass


class PricePredictModelFiles:

    def __init__(self, folder_path: str = None):
        self._folder_path = folder_path or Path.cwd() / 'file_management/price_predict_models'

        self._models = dict()

    def save_model(self, atype: AType, model: 'xgb.Booster'):
        import xgboost as xgb

        if not isinstance(model, xgb.Booster):
            raise TypeError(f"Price predict model is type {type(model)}. Expected {xgb.Booster}")

        self._folder_path.mkdir(parents=True, exist_ok=True)
        file_path = self._folder_path / f"{atype}.json"

        model.save_model(str(file_path))

    def load_model(self, atype: AType):
        import xgboost as xgb

        model = xgb.Booster()
        file_path = self._folder_path / f"{atype}.json"

        if os.path.getsize(file_path) <= 2:
            return None

        model = model.load_model(str(file_path))
        self._models[atype] = model

        return model


class CraftingSimulatorFiles:

    def __init__(self, folder_path: str = None):
        self._folder_path = folder_path or Path.cwd() / 'file_management/crafting_models'

        self._models = dict()

    def save_model(self, atype: str, ppo_model):
        from stable_baselines3 import PPO

        if not isinstance(ppo_model, PPO):
            raise TypeError(f"PPO model is type {type(ppo_model)}. Expected {PPO}")
        self._folder_path.mkdir(parents=True, exist_ok=True)

        file_path = self._folder_path / f"{atype}"
        ppo_model.save(file_path)

    def load_model(self, atype: str):
        from stable_baselines3 import PPO

        file_path = self._folder_path / f"{atype}.zip"

        if not os.path.exists(file_path):
            return None

        model = PPO.load(file_path)
        self._models[atype] = model
        return model


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)

