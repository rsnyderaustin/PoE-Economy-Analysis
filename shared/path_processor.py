import re
from pathlib import Path


class PathProcessor:

    def __init__(self, path: str | Path):
        self._path = path if isinstance(path, str) else str(path)

    @property
    def path(self):
        return self._path

    @staticmethod
    def create_relative_file_path(endpoint: str) -> Path:
        endpoint = endpoint.lstrip('/')
        project_path = Path.cwd()
        relative_path = project_path / endpoint
        return relative_path

    def attach_url_endpoint(self, endpoint: str):
        if '://' in self._path:
            protocol, url = self._path.split('://', 1)

            url = f"{url}/{endpoint}/"

            url = re.sub(r'/+', '/', url)

            full_url = f"{protocol}://{url}"
        else:
            full_url = f"{self._path}/{endpoint}"
            full_url = re.sub(r'/+', '/', full_url)

        self._path = full_url
        return self

    def attach_file_path_endpoint(self, endpoint: str):
        path = f"{self._path}/{endpoint}"
        self._path = re.sub(r'/+', '/', path)
        return self
