from sqlalchemy import Column, Integer, ForeignKey, String, Table
from sqlalchemy.orm import relationship

from deinemudda.persistence.entity import Base


class Setting(Base):
    """
    Data model of chat specific settings
    """
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="settings")

    key = Column(String, unique=True, index=True)
    value = Column(String)


association_table = Table('association', Base.metadata,
                          Column('chat_id', Integer, ForeignKey('chats.id')),
                          Column('user_id', Integer, ForeignKey('users.id')))


class Chat(Base):
    """
    Data model of a chat
    """
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
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
