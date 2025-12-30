
import logging
from abc import ABC
from enum import Enum
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

logging_path = Path.cwd() / 'shared/program_logging/logs/all_logs.log'
logging_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    filename=logging_path,
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s\n'
)


class LogFile(Enum):
    API_PARSING = Path.cwd() / 'shared/program_logging/logs/api_parsing.log'
    CRAFTING_MODEL = Path.cwd() / 'shared/program_logging/logs/crafting_model.log'
    STATS_PREP = Path.cwd() / 'shared/program_logging/logs/stats_prep.log'
    EXTERNAL_APIS = Path.cwd() / 'shared/program_logging/logs/external_apis.log'
    PSQL = Path.cwd() / 'shared/program_logging/logs/psql.log'
    PRICE_PREDICT_MODEL = Path.cwd() / 'shared/program_logging/logs/price_predict_model.log'
    INPUT_OUTPUT = Path.cwd() / 'shared/program_logging/logs/input_output.log'
    PROGRAM_OVERVIEW = Path.cwd() / 'shared/program_logging/logs/program_overview.log'


class Logger(ABC):

    def __init__(self,
                 log_name: LogFile | str,
                 rotate_logs: bool = True,
                 file_path: Path = None,
                 formatter: logging.Formatter = None
                 ):
        logger_name = log_name if isinstance(log_name, str) else log_name.name
        file_path = Path(file_path or log_name.value if isinstance(log_name, LogFile) else f'logs/{logger_name}.log')
        file_path.parent.mkdir(parents=True, exist_ok=True)

        formatter = formatter or logging.Formatter('%(asctime)s - %(levelname)s - %(message)s\n')

        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.INFO)
        self._logger.propagate = True

        # Only add handlers once
        if not self._logger.handlers:
            file_handler = TimedRotatingFileHandler(
                filename=file_path,
                when='midnight',  # or 'D' for daily
                interval=1,
                backupCount=7,  # keep 7 days of logs
                encoding='utf-8'
            ) if rotate_logs else logging.FileHandler(file_path)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

    def get_logger(self):
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

    def fetch_log(self, log_e: LogFile):
        if log_e not in self._logs:
            self._logs[log_e] = Logger(log_name=log_e).get_logger()

        return self._logs[log_e]



