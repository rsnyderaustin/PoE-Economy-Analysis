import logging
from abc import ABC
from enum import Enum
from pathlib import Path


logging.basicConfig(
    level=logging.INFO,
    filename=Path.cwd() / 'shared/logging/logs/all_logs.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s\n'
)


class LogFile(Enum):
    API_PARSING = Path.cwd() / 'shared/logging/logs/api_parsing.log'
    RESPONSE_TRACKING = Path.cwd() / 'shared/logging/logs/response_tracking.log'
    CRAFTING_MODEL = Path.cwd() / 'shared/logging/logs/crafting_model.log'
    STATS_PREP = Path.cwd() / 'shared/logging/logs/stats_prep.log'
    EXTERNAL_APIS = Path.cwd() / 'shared/logging/logs/external_apis.log'
    PSQL = Path.cwd() / 'shared/logging/logs/psql.log'
    PRICE_PREDICT_MODEL = Path.cwd() / 'shared/logging/logs/price_predict_model.log'


class Logger(ABC):

    def __init__(self, log_name: LogFile | str, file_path: Path = None, formatter: logging.Formatter = None):
        logger_name = log_name if isinstance(log_name, str) else log_name.name
        file_path = Path(file_path or log_name.value if isinstance(log_name, LogFile) else f'logs/{logger_name}.log')
        file_path.parent.mkdir(parents=True, exist_ok=True)

        formatter = formatter or logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n')

        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = True

        # Only add handlers once
        if not self._logger.handlers:
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(formatter)
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

        self._logs = self._create_loggers()

    @staticmethod
    def _create_loggers():
        logs = dict()
        for log_e in LogFile:
            log = Logger(log_name=log_e)
            logs[log_e] = log.get_logger()

        return logs

    def fetch_log(self, log_e: LogFile):
        return self._logs[log_e]



