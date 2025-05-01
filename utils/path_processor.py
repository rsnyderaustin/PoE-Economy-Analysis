import re
from pathlib import Path


class PathProcessor:

    def __init__(self, path: str):
        self.path = path

    @staticmethod
    def create_relative_file_path(endpoint: str) -> Path:
        endpoint = endpoint.lstrip('/')
        project_path = Path.cwd()
        relative_path = project_path / endpoint
        return relative_path

    def attach_url_endpoint(self, endpoint: str):
        if '://' in self.path:
            protocol, url = self.path.split('://', 1)

            url = f"{url}/{endpoint}/"

            url = re.sub(r'/+', '/', url)

            full_url = f"{protocol}://{url}"
        else:
            full_url = f"{self.path}/{endpoint}"
            full_url = re.sub(r'/+', '/', full_url)

        self.path = full_url
        return self

    def attach_file_path_endpoint(self, endpoint: str):
        path = f"{self.path}/{endpoint}"
        self.path = re.sub(r'/+', '/', path)
        return self
