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

from sqlalchemy import Column, Integer, String, DateTime, Boolean
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

    last_timeout = Column(DateTime)
    is_banned = Column(Boolean, default=False)

    chats = relationship(
        "Chat",
        secondary=association_table,
        back_populates="users",
        lazy='joined')
