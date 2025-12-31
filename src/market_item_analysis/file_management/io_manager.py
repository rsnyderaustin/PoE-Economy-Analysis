import json
from pathlib import Path
from typing import Any

import pandas as pd


def _write_jsonl(path: Path, records: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)

    with open(path, 'a', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')


def _load_jsonl(path: Path) -> 'Generator[dict[str, Any], None, None]':
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            yield json.loads(line)


class PoE2EconomyAnalysisIOManager:

    def __init__(self):
        self.raw_listings_path = Path.cwd() / 'file_management/dynamic_files/raw_listings.jsonl'
        self.constructed_listings_path = Path.cwd() / 'file_management/dynamic_files/constructed_listings.jsonl'

    def save_raw_listings(self, raw_listings: list[dict]):
        _write_jsonl(path=self.raw_listings_path,
                     records=raw_listings)

    def load_raw_listings(self):
        return _load_jsonl(path=self.raw_listings_path)

    def save_constructed_listings(self, constructed_listings: list[dict]):
        _write_jsonl(path=self.constructed_listings_path,
                     records=constructed_listings)

    def load_constructed_listings(self):
        return _load_jsonl(path=self.constructed_listings_path)

    def save_price_predictions_performance(self, df: pd.DataFrame):
        return NotImplemented


