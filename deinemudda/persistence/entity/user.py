from sqlalchemy import Column, Integer, String

from deinemudda.persistence.entity import Base


class User(Base):
    """
    Data model of a bot user
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    username = Column(String)
