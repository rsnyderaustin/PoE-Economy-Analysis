
import os

import dotenv


class EnvLoader:
    _instance = None
    _initialized = False

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(EnvLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        cls = self.__class__
        if cls._initialized:
            return

        dotenv.load_dotenv()

        cls._initialized = True

    def get_env(self, env_var: str):
        return os.getenv(env_var)

env_loader = EnvLoader()
