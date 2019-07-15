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

from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext
from telegram_click import generate_command_list
from telegram_click.argument import Argument, Selection
from telegram_click.decorator import command
from telegram_click.permission import GROUP_ADMIN, PRIVATE_CHAT

from deinemudda.config import AppConfig
from deinemudda.const import COMMAND_MUDDA, COMMAND_SET_ANTISPAM, COMMAND_SET_CHANCE, COMMAND_COMMANDS, COMMAND_STATS, \
    COMMAND_GET_SETTINGS, SETTINGS_TRIGGER_PROBABILITY_KEY, SETTINGS_ANTISPAM_ENABLED_KEY, \
    SETTINGS_ANTISPAM_ENABLED_DEFAULT, SETTINGS_TRIGGER_PROBABILITY_DEFAULT
from deinemudda.persistence import Persistence, Chat
from deinemudda.response import ResponseManager
from deinemudda.stats import MESSAGE_TIME, MESSAGES_COUNT, format_metrics
from deinemudda.util import send_message

# dictionary used for antispam-protection, if activated
spamtracker = {}

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class DeineMuddaBot:

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._config = config
        self._persistence = persistence
        self._response_manager = ResponseManager(self._persistence)

        self._updater = Updater(token=self._config.TELEGRAM_BOT_TOKEN.value,
                                use_context=True)

        handler_groups = {
            0: [MessageHandler(filters=None, callback=self._any_message_callback)],
            1: [MessageHandler(Filters.text, callback=self._message_callback),
                CommandHandler(
                    COMMAND_COMMANDS,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._commands_command_callback),
                CommandHandler(
                    COMMAND_STATS,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._stats_command_callback),
                CommandHandler(
                    COMMAND_MUDDA,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._mudda_command_callback),
                CommandHandler(
                    COMMAND_GET_SETTINGS,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._get_settings_command_callback),
                CommandHandler(
                    COMMAND_SET_ANTISPAM,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._set_antispam_command_callback),
                CommandHandler(
                    COMMAND_SET_CHANCE,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._set_chance_command_callback),
                MessageHandler(
                    filters=Filters.command & ~ Filters.reply,
                    callback=self._commands_command_callback)],
            2: [MessageHandler(
                filters=Filters.group & (~ Filters.reply) & (~ Filters.forwarded),
                callback=self._group_message_callback)],
        }

        for group, handlers in handler_groups.items():
            for handler in handlers:
                self._updater.dispatcher.add_handler(handler, group=group)

    def start(self):
        """
        Starts up the bot.
        This means filling the url pool and listening for messages.
        """
        self._updater.start_polling(clean=True)
        self._updater.idle()

    def stop(self):
        """
        Shuts down the bot.
        """
        self._updater.stop()

    def _shout(self, bot: Bot, message, text: str, reply: bool = True):
        shouting_text = "<b>{}!!!</b>".format(text.upper())

        reply_to_message_id = None
        if reply:
            reply_to_message_id = message.message_id

        send_message(bot, message.chat_id,
                     message=shouting_text,
                     parse_mode=ParseMode.HTML,
                     reply_to=reply_to_message_id)

    def _any_message_callback(self, update: Update, context: CallbackContext):
        chat_id = update.effective_message.chat_id
        chat_type = update.effective_chat.type

        chat = self._persistence.get_chat(chat_id)
        from_user = update.effective_message.from_user
        if chat is None:
            # make sure we know about this chat in persistence
            chat = Chat(id=chat_id, type=chat_type)
            chat.set_setting(SETTINGS_ANTISPAM_ENABLED_KEY, SETTINGS_ANTISPAM_ENABLED_DEFAULT)
            chat.set_setting(SETTINGS_TRIGGER_PROBABILITY_KEY, SETTINGS_TRIGGER_PROBABILITY_DEFAULT)
            self._persistence.add_or_update_chat(chat)

        # remember chat user
        self._persistence.add_or_update_chat_member(chat, from_user)

    @MESSAGE_TIME.time()
    def _message_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.effective_message.chat_id

        from_user = update.message.from_user
        chat = self._persistence.get_chat(chat_id)

        response_message = self._response_manager.find_matching_rule(chat, from_user.first_name, update.message.text)
        if response_message:
            self._shout(bot, update.message, response_message)

        MESSAGES_COUNT.labels(chat_id=chat_id).inc()

    def _group_message_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        effective_message = update.effective_message
        chat_id = effective_message.chat_id
        chat_type = update.effective_chat.type

        my_id = bot.get_me().id

        if effective_message.new_chat_members:
            for member in effective_message.new_chat_members:
                if member.id == my_id:
                    LOGGER.debug("Bot was added to group: {}".format(chat_id))
                    chat_entity = Chat(id=chat_id, type=chat_type)
                    self._persistence.add_or_update_chat(chat_entity)
                else:
                    LOGGER.debug("{} ({}) joined group {}".format(member.full_name, member.id, chat_id))
                    chat = self._persistence.get_chat(chat_id)
                    # remember chat user
                    self._persistence.add_or_update_chat_member(chat, member)

        if effective_message.left_chat_member:
            member = effective_message.left_chat_member
            if member.id == my_id:
                LOGGER.debug("Bot was removed from group: {}".format(chat_id))
                self._persistence.delete_chat(chat_id)
            else:
                LOGGER.debug("{} ({}) left group {}".format(member.full_name, member.id, chat_id))
                chat = self._persistence.get_chat(chat_id)
                chat.users = list(filter(lambda x: x.id != member.id, chat.users))
                self._persistence.add_or_update_chat(chat)

    def _antispam(self, update: Update, context: CallbackContext, n: int = 30):
        bot = context.bot
        chat_id = update.effective_message.chat_id

        chat = self._persistence.get_chat(chat_id)
        if chat is None:
            return
        anti_spam = chat.get_setting(SETTINGS_ANTISPAM_ENABLED_KEY, SETTINGS_ANTISPAM_ENABLED_DEFAULT)

        if anti_spam == "off":
            return False

        from_user = update.effective_message.from_user
        now = datetime.datetime.now()

        if from_user.id in spamtracker:
            difference = now - spamtracker[from_user.id][0]
            if difference < datetime.timedelta(seconds=n):
                warned = spamtracker[from_user.id][1]
                if warned:
                    try:
                        kicked = bot.kickChatMember(chat_id, from_user.id)
                        del spamtracker[from_user.id]
                        LOGGER.debug("Kicked: {}".format(kicked))
                    except Exception as ex:
                        LOGGER.debug("Error kicking user {}: {}".format(from_user.id, ex))
                else:
                    send_message(bot,
                                 chat_id,
                                 parse_mode=ParseMode.HTML,
                                 message="{}: <b>Stop spamming or I will kick you!</b>".format(from_user.name))
                    new_elem = {from_user.id: [now, True]}
                    spamtracker.update(new_elem)
                return True

        warned = False
        new_elem = {from_user.id: [now, warned]}
        spamtracker.update(new_elem)

        return False

    @command(
        name=COMMAND_COMMANDS,
        description="List commands supported by this bot.",
        permissions=PRIVATE_CHAT | GROUP_ADMIN
    )
    def _commands_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        text = generate_command_list(update, context)
        send_message(bot, chat_id, text, parse_mode=ParseMode.MARKDOWN)

    @command(
        name=COMMAND_STATS,
        description="List bot statistics.",
        permissions=PRIVATE_CHAT | GROUP_ADMIN
    )
    def _stats_command_callback(self, update: Update, context: CallbackContext) -> None:
        """
        /stats command handler
        :param update: the chat update object
        :param context: telegram context
        """
        bot = context.bot
        message = update.effective_message
        chat_id = update.effective_chat.id

        text = format_metrics()

        send_message(bot, chat_id, text, reply_to=message.message_id)

    @command(
        name=COMMAND_MUDDA,
        description="Trigger the bot manually.",
        permissions=PRIVATE_CHAT | GROUP_ADMIN
    )
    def _mudda_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        if self._antispam(update, context):
            try:
                LOGGER.debug("Trying to removing message {} in chat {} because of spam".format(message_id, chat_id))
                bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as ex:
                LOGGER.debug("Couldn't remove message: {}".format(ex))
            return

        text = "deine mudda"
        self._shout(bot, update.message, text, reply=False)

    @command(
        name=COMMAND_GET_SETTINGS,
        description="Show settings for the current chat.",
        permissions=PRIVATE_CHAT | GROUP_ADMIN
    )
    def _get_settings_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)

        lines = []
        for setting in chat.settings:
            lines.append("{}: {}".format(setting.key, setting.value))

        message = "\n".join(lines)
        if message:
            send_message(bot, chat_id, message)
        else:
            # TODO: would be better if this could display default values to give at least some information
            send_message(bot, chat_id, "No chat specific settings set")

    @command(
        name=COMMAND_SET_CHANCE,
        description="Set the trigger probability to a specific value.",
        arguments=[
            Argument(
                name="probability",
                example="0.13",
                type=float,
                converter=lambda x: float(x),
                description="The probability to set",
                validator=(lambda x: 0 <= x <= 1)
            )
        ],
        permissions=PRIVATE_CHAT | GROUP_ADMIN
    )
    def _set_chance_command_callback(self, update: Update, context: CallbackContext, probability):
        bot = context.bot
        chat_id = update.effective_message.chat_id

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting(SETTINGS_TRIGGER_PROBABILITY_KEY, str(probability))
        self._persistence.add_or_update_chat(chat)

        send_message(bot, chat_id, message="TriggerChance: {}%".format(probability * 100))

    @command(
        name=COMMAND_SET_ANTISPAM,
        description="Turn antispam feature on/off",
        arguments=[
            Selection(
                name="state",
                description="The new state",
                allowed_values=["on", "off"]
            )
        ],
        permissions=PRIVATE_CHAT | GROUP_ADMIN
    )
    def _set_antispam_command_callback(self, update: Update, context: CallbackContext, new_state: str):
        bot = context.bot
        chat_id = update.effective_message.chat_id

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting(SETTINGS_ANTISPAM_ENABLED_KEY, new_state)
        self._persistence.add_or_update_chat(chat)

        send_message(bot, chat_id, message="Antispam: {}".format(new_state))
