
import re

class StringProcessor:

    def __init__(self, string: str):
        self.string = string

    def attach_url_endpoint(self, endpoint: str):
        if '://' in self.string:
            protocol, url = self.string.split('://', 1)

            url = f"{url}/{endpoint}/"

            url = re.sub(r'/+', '/', url)

            full_url = f"{protocol}://{url}"
        else:
            full_url = f"{self.string}/{endpoint}"
            full_url = re.sub(r'/+', '/', full_url)

        self.string = full_url
        return self

    def attach_file_path_endpoint(self, endpoint: str):
        path = f"{self.string}/{endpoint}"
        self.string = re.sub(r'/+', '/', path)
        return self
