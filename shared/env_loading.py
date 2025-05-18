
import dotenv
import os


class EnvLoader:

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EnvLoader, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        if not getattr(self, '_initialized', False):
            dotenv.load_dotenv()

            self._initialized = True

    def get_env(self, env_var: str):
        return os.getenv(env_var)


env_loader = EnvLoader()

