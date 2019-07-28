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

from telegram import Update, ParseMode
from telegram.ext import CallbackContext

from deinemudda.config import AppConfig
from deinemudda.const import SETTINGS_ANTISPAM_ENABLED_KEY, SETTINGS_ANTISPAM_ENABLED_DEFAULT
from deinemudda.persistence import Persistence
from deinemudda.util import send_message

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

KEY_LAST_MESSAGE_TIME = "last_message_time"
KEY_HAS_BEEN_WARNED = "has_been_warned"


class AntiSpam:
    """
    Keeps track of messages from users to decide if someone is spamming commands
    """

    data = {}

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._config = config
        self._persistence = persistence
        self._duration = 30

    def process_message(self, update: Update, context: CallbackContext) -> bool:
        now = datetime.datetime.now()
        bot = context.bot
        chat_id = update.effective_message.chat_id
        from_user = update.effective_message.from_user

        if not self._is_spam(update, context):
            return False

        warned = self.data[from_user.id][KEY_HAS_BEEN_WARNED]
        if warned:
            try:
                kicked = bot.kickChatMember(chat_id, from_user.id)
                del self.data[from_user.id]
                LOGGER.debug("Kicked: {}".format(kicked))
            except Exception as ex:
                LOGGER.debug("Error kicking user {}: {}".format(from_user.id, ex))
        else:
            send_message(bot,
                         chat_id,
                         parse_mode=ParseMode.MARKDOWN,
                         message="{}: **Stop spamming or I will kick you!**".format(from_user.name))
            warned = True

        self._update_data(from_user.id, now, warned)
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
        now = datetime.datetime.now()
        if from_user.id in self.data:
            difference = now - self.data[from_user.id][KEY_LAST_MESSAGE_TIME]
            if difference < datetime.timedelta(seconds=self._duration):
                return True
        else:
            self._update_data(from_user.id, now, False)

        return False

    def _update_data(self, id: int, last_message_time: datetime, has_been_warned: bool):
        new_elem = {
            id: {
                KEY_LAST_MESSAGE_TIME: last_message_time,
                KEY_HAS_BEEN_WARNED: has_been_warned}
        }
        self.data.update(new_elem)
