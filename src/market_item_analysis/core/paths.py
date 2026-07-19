from pathlib import Path


class ProjectPathResolver:
    _ROOT = Path(__file__).parent.parent

    @classmethod
    def path(cls, folders: list[str], file_name: str | None = None) -> Path:
        folders = '/'.join(folders)
        folders_path = cls._ROOT / folders

        if file_name is not None:
            folders_path / file_name

        return folders_path

    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent.parent

        self.
ROOT_DIR =