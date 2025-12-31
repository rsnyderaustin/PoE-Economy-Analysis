import json
import os
import tempfile
from abc import ABC
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from src.market_item_analysis.shared.enums.item_enums import EquipmentCategory
from . import io_utils


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


class PoE2EconomyAnalysisDataManager:

    def __init__(self):
        self.raw_listings_path = Path.cwd() / 'file_management/dynamic_files/raw_listings.jsonl'
        self.constructed_listings_path = Path.cwd() / 'file_management/dynamic_files/constructed_listings.jsonl'

    def write_raw_listings(self, raw_listings: list[dict]):
        _write_jsonl(path=self.raw_listings_path,
                     records=raw_listings)

    def load_raw_listings(self):
        return _load_jsonl(path=self.raw_listings_path)

    def write_constructed_listings(self, constructed_listings: list[dict]):
        _write_jsonl(path=self.constructed_listings_path,
                     records=constructed_listings)

    def load_constructed_listings(self):
        return _load_jsonl(path=self.constructed_listings_path)
