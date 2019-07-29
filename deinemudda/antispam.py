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

    banned_users = set()
    timeouted_users = set()

    data = {}

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._config = config
        self._persistence = persistence

        self._spam_time_window = datetime.timedelta(seconds=1)
        self._spam_message_amount = 1
        self._user_timeout_duration = 30

    def process_message(self, update: Update, context: CallbackContext) -> bool:
        """
        Processes a message
        :param update: update
        :param context: callback context
        :return: true if the message is spam, false otherwise
        """
        now = datetime.datetime.now()
        bot = context.bot
        chat_id = update.effective_message.chat_id
        from_user = update.effective_message.from_user

        self._update_data(from_user.id, now)

        if not self._is_spam(update, context):
            return False

        # TODO: check the last time when the user has been timeouted, and if it is not long ago, kick/ban him instead of just timeouting
        self.timeout_user(from_user.id)

        # try:
        #     kicked = bot.kickChatMember(chat_id, from_user.id)
        #     LOGGER.debug("Kicked: {}".format(kicked))
        # except Exception as ex:
        #     LOGGER.debug("Error kicking user {}: {}".format(from_user.id, ex))

        return True

    def _is_spam(self, update: Update, context: CallbackContext) -> bool:
        """
        Checks if this message is spam
        :param update: message update
        :param context: callback context
        :return: true if spam, false otherwise
        """
        chat_id = update.effective_message.chat_id
        chat = self._persistence.get_chat(chat_id)
        if chat is None:
            return False
        anti_spam = chat.get_setting(SETTINGS_ANTISPAM_ENABLED_KEY, SETTINGS_ANTISPAM_ENABLED_DEFAULT)

        if anti_spam == "off":
            return False

        from_user = update.effective_message.from_user

        if from_user.id in self.timeouted_users:
            # TODO: check if timeout has expired
            return True

        if from_user.id in self.banned_users:
            return True

        message_count = len(self.data[from_user.id][KEY_LAST_MESSAGE_TIMES])
        if message_count >= self._spam_message_amount:
            return True

        return False

    def timeout_user(self, user_id: int):
        """
        Timeout a specific user
        :param user_id: the user id
        """
        # TODO: this should probably be persisted
        self.timeouted_users.add(user_id)

    def ban_user(self, user_id: int):
        """
        Ban a specific user
        :param user_id: the user id
        """
        # TODO: this should probably be persisted
        self.banned_users.add(user_id)

    def _update_data(self, user_id: int, latest_message_time: datetime):
        old_elem = self.data.get(user_id, None)
        if old_elem is None:
            message_times = []
        else:
            message_times = old_elem[KEY_LAST_MESSAGE_TIMES]

        # remove message times outside interesting window
        message_times = list(
            filter(lambda x: x < (latest_message_time - self._spam_time_window),
                   message_times)).append(latest_message_time)

        new_elem = {
            user_id: {
                KEY_LAST_MESSAGE_TIMES: message_times
            }
        }
        self.data.update(new_elem)
