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
import datetime
import logging

from telegram import Update
from telegram.ext import CallbackContext

from deinemudda.config import AppConfig
from deinemudda.const import SETTINGS_ANTISPAM_ENABLED_KEY, SETTINGS_ANTISPAM_ENABLED_DEFAULT
from deinemudda.persistence import Persistence

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

KEY_LAST_MESSAGE_TIMES = "last_message_times"
KEY_HAS_BEEN_WARNED = "has_been_warned"


class AntiSpam:
    """
    Keeps track of messages from users to decide if someone is spamming commands
    """

    data = {}

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._config = config
        self._persistence = persistence

        self._spam_time_window = datetime.timedelta(seconds=1)
        self._spam_message_amount = 5
        self._user_timeout_duration = 30

    def _enabled(self, chat_id: int) -> bool:
        chat = self._persistence.get_chat(chat_id)
        if chat is None:
            return False
        anti_spam = chat.get_setting(SETTINGS_ANTISPAM_ENABLED_KEY, SETTINGS_ANTISPAM_ENABLED_DEFAULT)
        return anti_spam == SETTINGS_ANTISPAM_ENABLED_DEFAULT

    def process_message(self, update: Update, context: CallbackContext) -> bool:
        """
        Processes a message
        :param update: update
        :param context: callback context
        :return: true if the message is spam, false otherwise
        """
        bot = context.bot
        chat_id = update.effective_message.chat_id

        if not self._enabled(chat_id):
            return False

        from_user = update.effective_message.from_user
        self._update_data(from_user.id)

        user_entity = self._persistence.get_user(from_user.id)

        # check if the user is banned
        if user_entity.is_banned:
            return True

        # check if the user has a timeout
        now = datetime.datetime.now()
        if user_entity.last_timeout is not None and user_entity.last_timeout >= now - datetime.timedelta(
                seconds=self._user_timeout_duration):
            return True

        # check if the message is spam
        is_spam = self._is_spam(update, context)

        if is_spam:
            if user_entity.last_timeout is None or user_entity.last_timeout < now - datetime.timedelta(
                    seconds=self._user_timeout_duration):
                self.timeout_user(from_user.id)
            else:
                try:
                    kicked = bot.kickChatMember(chat_id, from_user.id)
                    LOGGER.debug("Kicked: {}".format(kicked))
                except Exception as ex:
                    LOGGER.debug("Error kicking user {}: {}".format(from_user.id, ex))
                self.ban_user(from_user.id)

        return is_spam

    def _is_spam(self, update: Update, context: CallbackContext) -> bool:
        """
        Checks if this message is spam
        :param update: message update
        :param context: callback context
        :return: true if spam, false otherwise
        """
        from_user = update.effective_message.from_user

        message_count = len(self.data[from_user.id][KEY_LAST_MESSAGE_TIMES])
        if message_count >= self._spam_message_amount:
            return True

        return False

    def timeout_user(self, user_id: int):
        """
        Timeout a specific user
        :param user_id: the user id
        """
        user_entity = self._persistence.get_user(user_id)
        user_entity.last_timeout = datetime.datetime.now()
        self._persistence.add_or_update_user(user_entity)

    def ban_user(self, user_id: int):
        """
        Ban a specific user
        :param user_id: the user id
        """
        user_entity = self._persistence.get_user(user_id)
        user_entity.is_banned = True
        self._persistence.add_or_update_user(user_entity)

    def unban_user(self, user_id: int):
        """
        Un-Ban a specific user
        :param user_id: the user id
        """
        user_entity = self._persistence.get_user(user_id)
        user_entity.is_banned = False
        self._persistence.add_or_update_user(user_entity)

    def _update_data(self, user_id: int) -> dict:
        latest_message_time = datetime.datetime.now()
        old_elem = self.data.get(user_id, None)
        if old_elem is None:
            message_times = []
        else:
            message_times = old_elem[KEY_LAST_MESSAGE_TIMES]

        # remove message times outside interesting window
        message_times = list(filter(lambda x: x < (latest_message_time - self._spam_time_window), message_times))
        message_times.append(latest_message_time)

        new_elem = {
            user_id: {
                KEY_LAST_MESSAGE_TIMES: message_times
            }
        }
        self.data.update(new_elem)
        return new_elem
