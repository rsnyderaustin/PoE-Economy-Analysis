from enum import Enum
import dotenv
import os


class EnvVariable(Enum):
    POSSESSID = "POSSESSID"
    PSQL_HOST = "PSQL_HOST"
    PSQL_DATABASE = "PSQL_DATABASE"
    PSQL_USERNAME = "PSQL_USERNAME"
    PSQL_PASSWORD = "PSQL_PASSWORD"
    PSQL_TRAINING_TABLE = "PSQL_TRAINING_TABLE"


class EnvLoader:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EnvLoader, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not self._initialized:
            dotenv.load_dotenv()

            self._initialized = True

    def get_env(self, env_variable: EnvVariable):
        return os.getenv(env_variable.value)


env_loader = EnvLoader()

