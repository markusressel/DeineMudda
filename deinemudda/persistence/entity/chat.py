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

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint, BigInteger, Integer
from sqlalchemy.orm import relationship

from deinemudda.persistence.entity import Base


class Setting(Base):
    """
    Data model of chat specific settings
    """
    __tablename__ = 'settings'
    __table_args__ = (UniqueConstraint('chat_id', 'key', name='_setting_key_uc'),)

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="settings")

    key = Column(String, index=True)
    value = Column(String)


association_table = Table('association', Base.metadata,
                          Column('chat_id', BigInteger, ForeignKey('chats.id')),
                          Column('user_id', BigInteger, ForeignKey('users.id')))


class Chat(Base):
    """
    Data model of a chat
    """
    __tablename__ = 'chats'

    id = Column(BigInteger, primary_key=True)
    type = Column(String)
    users = relationship(
        "User",
        secondary=association_table,
        back_populates="chats",
        lazy='joined')
    settings = relationship(
        "Setting",
        back_populates="chat",
        single_parent=True,
        cascade="all, delete-orphan",
        lazy='joined')

    def get_setting(self, key: str, default: str) -> str:
        setting = list(filter(lambda x: x.key == key, self.settings))
        if len(setting) > 0:
            return setting[0].value
        else:
            return default

    def set_setting(self, key: str, value: str):
        setting = list(filter(lambda x: x.key == key, self.settings))
        if len(setting) > 0:
            setting[0].value = value
        else:
            new_setting = Setting(key=key, value=value)
            self.settings.append(new_setting)
