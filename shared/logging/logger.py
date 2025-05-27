
import logging
from abc import ABC
from enum import Enum
from pathlib import Path


class LogFile(Enum):
    API_PARSING = Path.cwd() / 'shared/logging/logs/api_parsing.log'
    RESPONSE_TRACKING = Path.cwd() / 'shared/logging/logs/response_tracking.log'
    CRAFTING_MODEL = Path.cwd() / 'shared/logging/logs/crafting_model.log'
    STATS_PREP = Path.cwd() / 'shared/logging/logs/stats_prep.log'
    EXTERNAL_APIS = Path.cwd() / 'shared/logging/logs/external_apis.log'
    OTHER = Path.cwd() / 'shared/logging/logs/other.log'


class Logger(ABC):

    def __init__(self, log_name: LogFile, formatter: logging.Formatter = None):
        self._log_name = log_name
        self._file_path = log_name.value
        self._formatter = formatter or logging.Formatter('%(asctime)s - %(message)s')

        self._logger = logging.getLogger(str(self._log_name))
        self._logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(self._file_path)
        file_handler.setFormatter(self._formatter)

        self._logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        return self._logger


class LogsHandler:
    _instance = None
    _initialized = False

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(LogsHandler, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self._logs = dict()

    def create_loggers(self):
        for log_e in LogFile:
            log = Logger(log_name=log_e)
            self._logs[log_e] = log.get_logger()

    def fetch_log(self, log_e: LogFile):
        return self._logs[log_e]



