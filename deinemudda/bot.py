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

import logging

from telegram import Bot, Update
from telegram.ext import MessageHandler, CommandHandler, filters
from telegram.ext._applicationbuilder import ApplicationBuilder
from telegram.ext._contexttypes import ContextTypes
from telegram_click import generate_command_list
from telegram_click.argument import Argument, Selection
from telegram_click.decorator import command
from telegram_click.permission import GROUP_ADMIN, PRIVATE_CHAT, GROUP_CREATOR, GROUP_CHAT
from telegram_click.permission.base import Permission

from deinemudda.antispam import AntiSpam
from deinemudda.config import AppConfig
from deinemudda.const import *
from deinemudda.persistence import Persistence, Chat
from deinemudda.response import ResponseManager
from deinemudda.stats import MESSAGE_TIME, MESSAGES_COUNT, format_metrics
from deinemudda.util import send_message

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class _ConfigAdmins(Permission):

    def __init__(self):
        self._config = AppConfig()

    async def evaluate(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        from_user = update.effective_message.from_user
        return from_user.username in self._config.TELEGRAM_ADMIN_USERNAMES.value


CONFIG_ADMINS = _ConfigAdmins()


class DeineMuddaBot:

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._antispam = AntiSpam(config, persistence)
        self._config = config
        self._persistence = persistence
        self._response_manager = ResponseManager(self._persistence)

        self._app = ApplicationBuilder().token(self._config.TELEGRAM_BOT_TOKEN.value).build()

        handler_groups = {
            0: [MessageHandler(filters=None, callback=self._any_message_callback)],
            1: [CommandHandler(
                COMMAND_HELP,
                filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                callback=self._help_command_callback),
                CommandHandler(
                    COMMAND_VERSION,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._version_command_callback),
                CommandHandler(
                    COMMAND_CONFIG,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._config_command_callback),
                CommandHandler(
                    COMMAND_STATS,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._stats_command_callback),
                CommandHandler(
                    COMMAND_MUDDA,
                    filters=(~ filters.FORWARDED),
                    callback=self._mudda_command_callback),
                CommandHandler(
                    COMMAND_LIST_USERS,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._list_users_command_callback),
                CommandHandler(
                    COMMAND_BAN,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._ban_command_callback),
                CommandHandler(
                    COMMAND_UNBAN,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._unban_command_callback),
                CommandHandler(
                    COMMAND_GET_SETTINGS,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._get_settings_command_callback),
                CommandHandler(
                    COMMAND_SET_ANTISPAM,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._set_antispam_command_callback),
                CommandHandler(
                    COMMAND_SET_CHANCE,
                    filters=(~ filters.FORWARDED) & (~ filters.REPLY),
                    callback=self._set_chance_command_callback),
                MessageHandler(filters.TEXT, callback=self._message_callback),
                MessageHandler(
                    filters=filters.COMMAND & ~ filters.REPLY,
                    callback=self._help_command_callback)],
            2: [MessageHandler(
                filters=filters.ChatType.GROUP & (~ filters.REPLY) & (~ filters.FORWARDED),
                callback=self._group_message_callback)],
        }

        for group, handlers in handler_groups.items():
            for handler in handlers:
                self._app.add_handler(handler, group=group)

    def start(self):
        """
        Starts up the bot.
        This means filling the url pool and listening for messages.
        """
        self._app.run_polling()

    def stop(self):
        """
        Shuts down the bot.
        """
        self._app.stop()

    async def _shout(self, bot: Bot, message, text: str, reply: bool or int = True):
        """
        Shouts a message into the given chat
        :param bot: bot object
        :param message: message object
        :param text: text to shout
        :param reply: True to reply to the message's user, int to reply to a specific message, False is no reply
        """
        shouting_text = f"<b>{text.upper()}!!!</b>"

        reply_to_message_id = None
        if reply:
            if isinstance(reply, bool):
                reply_to_message_id = message.message_id
            elif isinstance(reply, int):
                reply_to_message_id = reply
            else:
                raise AttributeError(f"Unsupported reply parameter: {reply}")

        await send_message(bot, message.chat_id,
                           message=shouting_text,
                           parse_mode="HTML",
                           reply_to=reply_to_message_id)

    async def _any_message_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        chat = self._persistence.get_chat(chat_id)
        self._persistence.add_or_update_chat_member(chat, from_user)

    @MESSAGE_TIME.time()
    async def _message_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        chat_id = update.effective_message.chat_id

        from_user = update.message.from_user
        chat = self._persistence.get_chat(chat_id)

        if len(update.message.text) not in self._config.CHAR_COUNT_RANGE.value:
            return

        if len(update.message.text.split()) not in self._config.WORD_COUNT_RANGE.value:
            return

        response_message = self._response_manager.find_matching_rule(chat, from_user.first_name, update.message.text)
        if response_message:
            await self._shout(bot, update.message, response_message)

        MESSAGES_COUNT.labels(chat_id=chat_id).inc()

    async def _group_message_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        effective_message = update.effective_message
        chat_id = effective_message.chat_id
        chat_type = update.effective_chat.type

        me = await bot.get_me()
        my_id = me.id

        if effective_message.new_chat_members:
            for member in effective_message.new_chat_members:
                if member.id == my_id:
                    LOGGER.debug(f"Bot was added to group: {chat_id}")
                    chat_entity = Chat(id=chat_id, type=chat_type)
                    self._persistence.add_or_update_chat(chat_entity)
                else:
                    LOGGER.debug(f"{member.full_name} ({member.id}) joined group {chat_id}")
                    chat = self._persistence.get_chat(chat_id)
                    # remember chat user
                    self._persistence.add_or_update_chat_member(chat, member)

        if effective_message.left_chat_member:
            member = effective_message.left_chat_member
            if member.id == my_id:
                LOGGER.debug(f"Bot was removed from group: {chat_id}")
                self._persistence.delete_chat(chat_id)
            else:
                LOGGER.debug(f"{member.full_name} ({member.id}) left group {chat_id}")
                chat = self._persistence.get_chat(chat_id)
                chat.users = list(filter(lambda x: x.id != member.id, chat.users))
                self._persistence.add_or_update_chat(chat)

    @command(
        name=COMMAND_HELP,
        description="List commands supported by this bot.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _help_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        text = await generate_command_list(update, context)
        await send_message(bot, chat_id, text, parse_mode="MARKDOWN")

    @command(
        name=COMMAND_VERSION,
        description="Show application version.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _version_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id
        text = f"Version: `{DEINE_MUDDA_VERSION}`"
        await send_message(bot, chat_id, text, parse_mode="MARKDOWN", reply_to=message_id)

    @command(
        name=COMMAND_CONFIG,
        description="Show current application configuration.",
        permissions=PRIVATE_CHAT & CONFIG_ADMINS
    )
    async def _config_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from container_app_conf.formatter.toml import TomlFormatter

        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        text = self._config.print(formatter=TomlFormatter())
        text = f"```\n{text}\n```"
        await send_message(bot, chat_id, text, parse_mode="MARKDOWN", reply_to=message_id)

    @command(
        name=COMMAND_STATS,
        description="List bot statistics.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _stats_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        /stats command handler
        :param update: the chat update object
        :param context: telegram context
        """
        bot = context.bot
        message_id = update.effective_message.message_id
        chat_id = update.effective_message.chat_id

        text = format_metrics()

        await send_message(bot, chat_id, text, reply_to=message_id)

    @command(
        name=COMMAND_MUDDA,
        description="Trigger the bot manually.",
        permissions=PRIVATE_CHAT | GROUP_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _mudda_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        if self._antispam.process_message(update, context):
            return

        text = "deine mudda"

        reply_to_message = update.message.reply_to_message
        if reply_to_message is not None:
            if not reply_to_message.from_user.is_bot \
                    and reply_to_message.from_user.id != update.message.from_user.id:
                reply = reply_to_message.message_id
            else:
                # ignore reply
                LOGGER.debug(
                    f"Ignoring /mudda call on reply to message {reply_to_message.message_id}: {reply_to_message.text}")
                return
        else:
            reply = False

        await self._shout(bot, update.message, text, reply=reply)

    @command(
        name=COMMAND_GET_SETTINGS,
        description="Show settings for the current chat.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _get_settings_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)

        lines = []
        for setting in chat.settings:
            lines.append(f"{setting.key}: {setting.value}")

        message = "\n".join(lines)
        if message:
            await send_message(bot, chat_id, message, reply_to=message_id)
        else:
            # TODO: would be better if this could display default values to give at least some information
            await send_message(bot, chat_id, "No chat specific settings set", reply_to=message_id)

    @command(
        name=COMMAND_SET_CHANCE,
        description="Set the trigger probability to a specific value.",
        arguments=[
            Argument(
                name=["probability", "p"],
                example="0.13",
                type=float,
                converter=lambda x: float(x),
                description="The probability to set",
                validator=(lambda x: 0 <= x <= 1)
            )
        ],
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _set_chance_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                           probability: float):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting(SETTINGS_TRIGGER_PROBABILITY_KEY, str(probability))
        self._persistence.add_or_update_chat(chat)

        await send_message(bot, chat_id, message=f"TriggerChance: {probability * 100}%", reply_to=message_id)

    @command(
        name=COMMAND_SET_ANTISPAM,
        description="Turn antispam feature on/off",
        arguments=[
            Selection(
                name=["state", "s"],
                description="The new state",
                allowed_values=["on", "off"]
            )
        ],
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _set_antispam_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, state: str):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting(SETTINGS_ANTISPAM_ENABLED_KEY, state)
        self._persistence.add_or_update_chat(chat)

        await send_message(bot, chat_id, message=f"Antispam: {state}", reply_to=message_id)

    @command(
        name=COMMAND_LIST_USERS,
        description="List all known users in this chat",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _list_users_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)
        message = "\n".join(
            list(map(lambda x: f"{x.id}: {x.username}" + (" (BANNED)" if x.is_banned else ""), chat.users)))

        await send_message(bot, chat_id, message=message, reply_to=message_id)

    @command(
        name=COMMAND_BAN,
        description="Ban a user",
        arguments=[
            Argument(
                name=["user", "u"],
                description="Username or user id",
                type=str,
                example="123456789",
            )
        ],
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _ban_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: str):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        try:
            user_id = int(user)
            user_entity = self._persistence.get_user(user_id)
        except:
            user_entity = self._persistence.get_user_by_username(user)

        if user_entity is None:
            await send_message(bot, chat_id, message=f"User {user} is unknown", reply_to=message_id)
            return

        user_id = user_entity.id
        username = user_entity.username
        user_entity.is_banned = True
        self._persistence.add_or_update_user(user_entity)

        await send_message(bot, chat_id, message=f"Banned user: {username} ({user_id})",
                           reply_to=message_id)

    @command(
        name=COMMAND_UNBAN,
        description="Unban a banned user",
        arguments=[
            Argument(
                name=["user", "u"],
                description="Username or user id",
                type=str,
                example="123456789",
            )
        ],
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    async def _unban_command_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user: str):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        try:
            user_id = int(user)
            user_entity = self._persistence.get_user(user_id)
        except:
            user_entity = self._persistence.get_user_by_username(user)

        if user_entity is None:
            await send_message(bot, chat_id, message=f"User {user} is unknown", reply_to=message_id)
            return

        user_id = user_entity.id
        username = user_entity.username
        user_entity.is_banned = False
        self._persistence.add_or_update_user(user_entity)

        await send_message(bot, chat_id,
                           message=f"Unbanned user: {username} ({user_id})",
                           reply_to=message_id)
