from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from deinemudda.persistence.entity import Base
from deinemudda.persistence.entity.chat import association_table


class User(Base):
    """
    Data model of a bot user
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    username = Column(String)
    first_name = Column(String)
    full_name = Column(String)

    chats = relationship(
        "Chat",
        secondary=association_table,
        back_populates="users",
        lazy='joined')
