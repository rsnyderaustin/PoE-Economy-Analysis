import os

from . import io_utils


class FilesManager:
    _instance = None
    _initialized = None

    def __new__(cls):
        if not getattr(cls, '_instance', None):
            cls._instance = super(FilesManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return

        self.file_data = io_utils.load_data_files()
        self.model_data = io_utils.load_models()

        self._initialized = True

    def _get_path_data(self, path_e: io_utils.DataPath | io_utils.ModelPath):
        if isinstance(path_e, io_utils.DataPath):
            return self.file_data[path_e]
        elif isinstance(path_e, io_utils.ModelPath):
            return self.model_data[path_e]
        else:
            raise TypeError(f"Received unexpected type {type(path_e)}")

    def has_data(self, path_e: io_utils.DataPath | io_utils.ModelPath):
        file_size = os.path.getsize(path_e.value)

        if path_e.value.suffix == '.json':
            return file_size >= 2
        else:
            return file_size > 0

    def save_data(self, paths: list[io_utils.DataPath | io_utils.ModelPath] = None):
        if not paths:
            data_paths = [path_e.value for path_e in io_utils.DataPath]
            model_paths = [path_e.value for path_e in io_utils.ModelPath]
            paths = [*data_paths, *model_paths]

        for path_e in paths:
            io_utils.write_to_file(data=self._get_path_data(path_e),
                                file_path=path_e.value)




