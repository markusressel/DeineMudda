#  Copyright (c) 2019 Markus Ressel
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.util.compat import contextmanager

from deinemudda.config import AppConfig
from deinemudda.persistence.entity.chat import Chat
from deinemudda.persistence.entity.user import User
from deinemudda.stats import ENTITIES_COUNT, USERS_IN_CHAT_COUNT

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
            session.merge(chat)
        self._update_stats()

    def add_or_update_chat_member(self, chat: Chat, user: User) -> None:
        user_entity = User(
            id=user.id,
            first_name=user.first_name,
            full_name=user.full_name,
            username=user.username
        )
        # remove old data
        chat.users = list(filter(lambda x: x.id != user_entity.id, chat.users))
        # add new
        chat.users.append(user_entity)
        # save
        self.add_or_update_chat(chat)

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

    def get_user_by_username(self, username: str) -> User or None:
        with self._session_scope() as session:
            return session.query(User).filter_by(username=username).one_or_none()

    def add_or_update_user(self, user: User) -> None:
        with self._session_scope(write=True) as session:
            session.add(user)
        self._update_stats()

    def is_response_bad(self, message: str, response: str) -> bool:
        # TODO: check if message/response combo is marked as bad
        return False

    def _update_stats(self):
        with self._session_scope() as session:
            chat_count = session.query(Chat).count()
            user_count = session.query(User).count()

            ENTITIES_COUNT.labels(type='chat').set(chat_count)
            ENTITIES_COUNT.labels(type='user').set(user_count)

            chats = session.query(Chat).all()
            for chat in chats:
                USERS_IN_CHAT_COUNT.labels(chat_id=chat.id).set(len(chat.users))
