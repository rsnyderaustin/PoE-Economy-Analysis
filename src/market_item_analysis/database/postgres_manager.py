from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from src.market_item_analysis.core.env_loader import EnvLoader


class PostgresDatabaseUrl:

    def __init__(self,
                 user: str | None = None,
                 password: str | None = None,
                 port: str | None = None,
                 database: str | None = None,
                 ip_address: str | None = None):
        e = EnvLoader()

        self.user = user or e.get_env("PSQL_USERNAME")
        self.password = password or e.get_env("PSQL_PASSWORD")
        self.port = port or e.get_env("PSQL_PORT")
        self.database = database or e.get_env("PSQL_DATABASE")
        self.ip_address = ip_address or e.get_env("PSQL_IP")

    @property
    def url(self):
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.ip_address}:{self.port}/{self.database}"


class PostgresManager:

    def __init__(self, db_url: PostgresDatabaseUrl):
        # Create the engine
        self.engine = create_engine(db_url.url, echo=False)
        # Create the session factory
        self.SessionLocal = sessionmaker(bind=self.engine)

    @contextmanager
    def get_session(self):
        """Provide a transactional scope around a series of operations."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
