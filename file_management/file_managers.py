import json
import os
import tempfile
from abc import ABC
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from shared.enums.item_enums import AType
from . import i_o_utils


class RawListingsFile:

    def __init__(self, path: Path = None):
        self._path = path or Path.cwd() / 'file_management/dynamic_files/raw_listings.jsonl'

    def save(self, new_records: list[dict]):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(exist_ok=True)

        with open(self._path, 'a', encoding='utf-8') as f:
            for record in new_records:
                json.dump(record, f)
                f.write('\n')

    def load(self) -> 'Generator[dict[str, Any], None, None]':
        with open(self._path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                yield json.loads(line)


class _JsonDictFile(ABC):

    def __init__(self, path: Path = None):
        self._path = path

    def save(self, data):
        i_o_utils.write_json(path=self._path, data=data)

    def load(self, default: Any = None):
        return i_o_utils.load_json(path=self._path, default=default)


class ListingStringsFile(_JsonDictFile):
    def __init__(self, path: Path = None):
        super().__init__(path or Path.cwd() / 'file_management/dynamic_files/listing_strings.json')


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

    _missing_data_msg = f"missing_ok is False when there is no data for class {__name__}"

    def __init__(self, path: Path = None):
        self._path = path or 'default_pkl_file.filetype'

        self._path.parent.mkdir(parents=True, exist_ok=True)  # ensure directory exists
        self._path.touch(exist_ok=True) # ensure file exists

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
            try:
                data = pickle.load(file)
                self._data = data
            except EOFError:
                if not missing_ok:
                    raise

                self._data = default

        return self._data


class ItemModsFile(PickleFile):

    def __init__(self, path: Path = None):
        super().__init__(path or Path.cwd() / 'file_management/dynamic_files/item_mods.pkl')

    def load(self, default: Any = None, missing_ok: bool = True) -> dict:
        return super().load(default=default, missing_ok=missing_ok)


class Poe2DbModsManagerFile(PickleFile):

    _missing_data_msg = "Could not load Poe2DbModsManager. May need to scrape Poe2Db."

    def __init__(self, path: Path = None):
        super().__init__(path or Path.cwd() / 'file_management/static_files/poe2db_mods_manager.pkl')

    def load(self, default: Any = None, missing_ok: bool = True) -> 'Poe2DbModsManager':
        return super().load(default=default, missing_ok=missing_ok)


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

        model.load_model(str(file_path))
        self._models[atype] = model

        return model


class CraftingSimulatorFiles:

    def __init__(self, folder_path: str = None):
        self._folder_path = folder_path or Path.cwd() / 'file_management/crafting_models'

    def save_model(self, atype: AType, model):
        from stable_baselines3 import PPO

        if not isinstance(model, PPO):
            raise TypeError(f"PPO model is type {type(model)}. Expected {PPO}")
        self._folder_path.mkdir(parents=True, exist_ok=True)

        file_path = self._folder_path / f"{atype}"
        model.save(file_path)

    def load_model(self, atype: AType) -> Optional['PPO']:
        from stable_baselines3 import PPO

        file_path = self._folder_path / f"{atype}.zip"

        if not os.path.exists(file_path):
            return None

        model = PPO.load(file_path)

        return model


class PricePredictCacheFile(PickleFile):

    def __init__(self, path: Path = None):
        super().__init__(path or Path.cwd() / 'file_management/temp_files/pp_training_cache.pkl')


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


class PricePredictPerformanceFile:

    def __init__(self, path: Path = None):
        self.path = path or Path.cwd() / 'file_management/temp_files/price_predict_performance.csv'

    def load(self, default: Any = None, missing_ok: bool = True) -> 'pd.DataFrame':
        import pandas as pd
        """
        Load performance data from CSV into a DataFrame.
        If the file does not exist, returns the default value or raises an error.
        """
        if not self.path.exists():
            if missing_ok:
                return default
            else:
                raise FileNotFoundError(f"File not found at path: {self.path}")

        try:
            return pd.read_csv(self.path)
        except Exception as e:
            print(f"Error loading file: {e}")
            return default

    def save(self, df: 'pd.DataFrame'):
        """
        Save the provided DataFrame to a CSV file.
        Creates parent directories if they do not exist.
        """
        import pandas as pd
        self.path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.path, index=False)


