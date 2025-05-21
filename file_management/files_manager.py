import os

from . import utils


class FilesManager:

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls.instance = super(FilesManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        self.file_data = utils.load_data_files()
        self.model_data = utils.load_models()

        self._initialized = True

    def _get_path_data(self, path_e: utils.DataPath | utils.ModelPath):
        if isinstance(path_e, utils.DataPath):
            return self.file_data[path_e]
        elif isinstance(path_e, utils.ModelPath):
            return self.model_data[path_e]
        else:
            raise TypeError(f"Received unexpected type {type(path_e)}")

    def has_data(self, path_e: utils.DataPath | utils.ModelPath):
        file_size = os.path.getsize(path_e.value)

        if path_e.value.suffix == '.json':
            return file_size >= 2
        else:
            return file_size > 0

    def save_data(self, paths: list[utils.DataPath | utils.ModelPath] = None):
        if not paths:
            data_paths = [path_e.value for path_e in utils.DataPath]
            model_paths = [path_e.value for path_e in utils.ModelPath]
            paths = [*data_paths, *model_paths]

        for path_e in paths:
            utils.write_to_file(data=self._get_path_data(path_e),
                                file_path=path_e.value)




