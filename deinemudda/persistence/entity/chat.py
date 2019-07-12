from sqlalchemy import Column, Integer, PickleType, Table, ForeignKey
from sqlalchemy.orm import relationship

from deinemudda.persistence.entity import Base


class SettingsPickleType(PickleType):
    trigger_chance = Integer


association_table = Table('association', Base.metadata,
                          Column('chat_id', Integer, ForeignKey('chats.id')),
                          Column('user_id', Integer, ForeignKey('users.id')))


class Chat(Base):
    """
    Data model of a chat
    """
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True)
    users = relationship(
        "User",
        secondary=association_table,
        back_populates="chats",
        lazy='joined')
    settings = Column(SettingsPickleType())
