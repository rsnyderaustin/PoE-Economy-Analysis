
from dotenv import load_dotenv
import os

from .env_enums import EnvVar


load_dotenv()


class EnvLoader:

    @staticmethod
    def get_env(env_variable: EnvVar, default=None):
        return os.getenv(env_variable.value, default)



