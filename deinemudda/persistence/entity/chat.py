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

from sqlalchemy import Column, Integer, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import relationship

from deinemudda.persistence.entity import Base


class Setting(Base):
    """
    Data model of chat specific settings
    """
    __tablename__ = 'settings'
    __table_args__ = (UniqueConstraint('chat_id', 'key', name='_setting_key_uc'),)

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="settings")

    key = Column(String, index=True)
    value = Column(String)


class VoteMenuItemVoter(Base):
    """
    Data model of chat specific settings
    """
    __tablename__ = 'vote_menu_item_voters'
    __table_args__ = (UniqueConstraint('vote_menu_item_id', 'user_id', name='_vote_menu_item_voter_uc'),)

    id = Column(Integer, primary_key=True)
    vote_menu_item_id = Column(Integer, ForeignKey('vote_menu_items.id'))
    vote_menu_item = relationship("VoteMenuItem", back_populates="voters")

    user_id = Column(Integer)
    count = Column(Integer)


class VoteMenuItem(Base):
    """
    Data model of chat specific settings
    """
    __tablename__ = 'vote_menu_items'
    __table_args__ = (UniqueConstraint('vote_menu_id', 'id', name='_vote_menu_item_uc'),)

    id = Column(String, primary_key=True)
    vote_menu_id = Column(Integer, ForeignKey('vote_menus.id'))
    vote_menu = relationship("VoteMenu", back_populates="items")

    text = Column(String)
    voters = relationship(
        "VoteMenuItemVoter",
        back_populates="vote_menu_item",
        single_parent=True,
        cascade="all, delete-orphan",
        lazy='joined')


class VoteMenu(Base):
    """
    Data model of chat specific vote_menus
    """
    __tablename__ = 'vote_menus'

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey('chats.id'))
    chat = relationship("Chat", back_populates="vote_menus")

    message_id = Column(Integer)
    items = relationship(
        "VoteMenuItem",
        back_populates="vote_menu",
        single_parent=True,
        cascade="all, delete-orphan",
        lazy='joined')

    def vote(self, user_id: int, item_id: str):
        """
        Vote for a specific VoteMenuItem
        :param user_id: id of the user that is voting
        :param item_id: id of the item to vote for
        """
        items = list(filter(lambda x: x.id == item_id, self.items))
        if len(items) > 0:
            item = items[0]
            voters = list(filter(lambda x: x.user_id == user_id, item.voters))
            if len(voters) > 0:
                voter = voters[0]
                voter.count += 1
            else:
                voter = VoteMenuItemVoter(user_id=user_id, count=1)
                item.voters.append(voter)
        else:
            raise ValueError(
                "VoteMenuItem with id '{}' not found in VoteMenu of message {}".format(item_id, self.message_id))

    def revoke_vote(self, user_id: int, item_id: str):
        """
        Revoke a vote for a specific VoteMenuItem
        :param user_id: id of the user that is voting
        :param item_id: id of the item to vote for
        """
        items = list(filter(lambda x: x.id == item_id, self.items))
        if len(items) > 0:
            item = items[0]
            voters = list(filter(lambda x: x.user_id == user_id, item.voters))
            if len(voters) > 0:
                voter = voters[0]
                voter.count -= 1
            else:
                voter = VoteMenuItemVoter(user_id, count=1)
                item.voters.append(voter)
            # filter out users without votes
            item.voters = list(filter(lambda x: x.count <= 0, item.voters))
        else:
            raise ValueError(
                "VoteMenuItem with id '{}' not found in VoteMenu of message {}".format(item_id, self.message_id))


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
    vote_menus = relationship(
        "VoteMenu",
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

    def get_vote_menu(self, message_id: int) -> VoteMenu or None:
        message_id = int(message_id)
        vote_menus = list(filter(lambda x: x.message_id == message_id, self.vote_menus))
        if len(vote_menus) > 0:
            return vote_menus[0]
        else:
            return None

    def add_or_update_vote_menu(self, menu: VoteMenu):
        self.vote_menus.append(menu)
