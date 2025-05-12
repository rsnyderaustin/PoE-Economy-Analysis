import pickle
from pathlib import Path
from typing import Any
import json
import os

import xgboost as xgb


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


def _write_json(data, file_path, disable_temp):
    if isinstance(data, xgb.Booster):
        data.save_model(file_path)
    else:
        new_path = file_path if disable_temp else file_path.with_suffix(file_path.suffix + ".tmp")
        with open(new_path, 'w') as training_data_json_path:
            json.dump(data, training_data_json_path, indent=4, cls=SetEncoder)
            training_data_json_path.flush()
            os.fsync(training_data_json_path.fileno())
        if not disable_temp:
            os.replace(new_path, file_path)

def write_to_file(file_path: Path, data, disable_temp: bool = False):
    if file_path.suffix == '.json':
        _write_json(data=data, file_path=file_path, disable_temp=disable_temp)
    elif file_path.suffix == '.csv':
        data.to_csv(file_path)
    elif file_path.suffix == '.pkl':
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
    else:
        raise ValueError(f"Unsupported file type {file_path.suffix}")


