import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.util.compat import contextmanager

from deinemudda.config import AppConfig
from deinemudda.persistence.entity.chat import Chat
from deinemudda.persistence.entity.user import User
from deinemudda.stats import ENTITIES_COUNT

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class Persistence:

    def __init__(self, config: AppConfig):
        url = config.SQL_PERSISTENCE_URL.value

        # TODO: this currently also logs to file because of alembic
        self._migrate_db(url)

        self._engine = create_engine(url, echo=False)
        self._sessionmaker = sessionmaker(bind=self._engine)

        self._update_stats()

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

    def get_chat(self, entity_id: int) -> Chat:
        with self._session_scope() as session:
            return session.query(Chat).get(entity_id)

    def add_or_update_chat(self, chat: Chat) -> None:
        with self._session_scope(write=True) as session:
            session.add(chat)
        self._update_stats()

    def delete_chat(self, entity_id: int) -> None:
        with self._session_scope(write=True) as session:
            chat = session.query(Chat).filter_by(id=entity_id).first()
            session.query(Chat).filter_by(id=entity_id).delete()
            if chat is not None:
                # delete orphans (users without any chat)
                for user in chat.users:
                    chat = session.query(Chat, User).filter(Chat.users.any(id=user.id)).first()
                    if chat is None:
                        user.delete()
        self._update_stats()

    def get_user(self, entity_id: int) -> User:
        with self._session_scope() as session:
            return session.query(User).get(entity_id)

    def add_or_update_user(self, user: User) -> None:
        with self._session_scope(write=True) as session:
            session.add(user)
        self._update_stats()

    def _update_stats(self):
        with self._session_scope() as session:
            chat_count = session.query(Chat).count()
            user_count = session.query(User).count()

            ENTITIES_COUNT.labels(type='chat').set(chat_count)
            ENTITIES_COUNT.labels(type='user').set(user_count)
