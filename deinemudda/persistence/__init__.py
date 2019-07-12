import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.util.compat import contextmanager

from deinemudda.config import AppConfig
from deinemudda.persistence.entity.user import User

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class Persistence:

    def __init__(self, config: AppConfig):
        url = config.SQL_PERSISTENCE_URL.value

        # TODO: this currently also logs to file because of alembic
        self._migrate_db(url)

        self._engine = create_engine(url, echo=False)
        self._sessionmaker = sessionmaker(bind=self._engine)

    @staticmethod
    def _migrate_db(url: str):
        from alembic.config import Config
        import alembic.command

        config = Config('alembic.ini')
        config.set_main_option('sqlalchemy.url', url)
        config.attributes['configure_logger'] = False

        alembic.command.upgrade(config, 'head')

    @contextmanager
    def _session_scope(self, write: bool = False) -> Session:
        """Provide a transactional scope around a series of operations."""
        session = self._sessionmaker()
        try:
            yield session
            if write:
                session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def add(self, user: User):
        with self._session_scope(write=True) as session:
            session.add(user)
