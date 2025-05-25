import os
from stable_baselines3 import PPO
import xgboost as xgb

from . import io_utils
from .io_utils import DataPath, ModelPath


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

        self.file_data = io_utils.load_data_files()

        self._initialized = True

    def _get_path_data(self, path_e: io_utils.DataPath):
        if isinstance(path_e, io_utils.DataPath):
            return self.file_data[path_e]
        else:
            raise TypeError(f"Received unexpected type {type(path_e)}")

    def has_data(self, path_e: io_utils.DataPath):
        if isinstance(path_e, ModelPath):
            raise TypeError(f"Type {ModelPath.__class__} not supported. Use model-specific functions in FilesManager.")

        file_size = os.path.getsize(path_e.value)

        if path_e.value.suffix == '.json':
            return file_size >= 2
        else:
            return file_size > 0

    def save_data(self, paths: list[io_utils.DataPath] = None):
        if not paths:
            data_paths = [path_e.value for path_e in io_utils.DataPath]
            model_paths = [path_e.value for path_e in io_utils.ModelPath]
            paths = [*data_paths, *model_paths]

        for path_e in paths:
            io_utils.write_to_file(data=self._get_path_data(path_e),
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



