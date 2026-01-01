import json
from pathlib import Path
from typing import Any


def _write_jsonl(path: Path, records: list[dict]):
    with open(path, 'a', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record) + '\n')


def _load_jsonl(path: Path) -> 'Generator[dict[str, Any], None, None]':
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            yield json.loads(line)

def _ensure_parent_directory(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)


class IoManager:

    def __init__(self):
        self.raw_listings_path = Path.cwd() / 'file_management/dynamic_files/raw_listings.jsonl'
        _ensure_parent_directory(self.raw_listings_path)

    def save_raw_responses(self, raw_listings: list[dict]):
        _write_jsonl(path=self.raw_listings_path,
                     records=raw_listings)

    def load_raw_responses(self) -> list[dict]:
        return _load_jsonl(path=self.raw_listings_path)
