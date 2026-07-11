import json
from pathlib import Path
from typing import Any


class InputOutputService:

    @classmethod
    def _ensure_parent_directory(cls, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    @classmethod
    def from_jsonl(cls, path: Path) -> Generator[dict[str, Any], None, None]:
        with open(path, 'r', encoding='utf-8') as f:
            for i, record in enumerate(f):
                yield json.loads(record)

    @classmethod
    def to_jsonl(cls, records: list[dict], path: Path):
        with open(path, 'a', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

