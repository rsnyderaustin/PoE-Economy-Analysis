import json
import os
import tempfile
from pathlib import Path
from typing import Any


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return super().default(obj)


def write_json(path: Path, data: dict):
    with tempfile.NamedTemporaryFile(mode='wb' if path.suffix == '.pkl' else 'w',
                                     dir=path.parent,
                                     delete=False,
                                     suffix=path.suffix,
                                     encoding='utf-8' if path.suffix in {'.json', '.csv'} else None) as tmp:
        tmp_path = Path(tmp.name)

        json.dump(data, tmp, indent=2, cls=SetEncoder)

        os.replace(tmp_path, path)


def load_json(path: Path, default: Any = None):
    with open(path, encoding='utf-8') as file:
        try:
            return json.load(file)
        except json.decoder.JSONDecodeError:
            if default is not None:
                return default
            else:
                raise

