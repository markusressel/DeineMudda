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

from telegram import Bot, Update, ParseMode, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext, CallbackQueryHandler
from telegram_click import generate_command_list
from telegram_click.argument import Argument, Selection
from telegram_click.decorator import command
from telegram_click.permission import GROUP_ADMIN, PRIVATE_CHAT, GROUP_CREATOR
from telegram_click.permission.base import Permission

from deinemudda.antispam import AntiSpam
from deinemudda.config import AppConfig
from deinemudda.const import COMMAND_MUDDA, COMMAND_SET_ANTISPAM, COMMAND_SET_CHANCE, COMMAND_COMMANDS, COMMAND_STATS, \
    COMMAND_GET_SETTINGS, SETTINGS_TRIGGER_PROBABILITY_KEY, SETTINGS_ANTISPAM_ENABLED_KEY, \
    SETTINGS_ANTISPAM_ENABLED_DEFAULT, SETTINGS_TRIGGER_PROBABILITY_DEFAULT, COMMAND_VERSION, DEINE_MUDDA_VERSION, \
    COMMAND_CONFIG, VOTE_BUTTON_ID_THUMBS_UP, VOTE_BUTTON_ID_THUMBS_DOWN
from deinemudda.persistence import Persistence, Chat
from deinemudda.persistence.entity.chat import VoteMenu, VoteMenuItem
from deinemudda.response import ResponseManager
from deinemudda.stats import MESSAGE_TIME, MESSAGES_COUNT, format_metrics
from deinemudda.util import send_message, build_menu

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class _ConfigAdmins(Permission):

    def __init__(self):
        self._config = AppConfig()

    def evaluate(self, update: Update, context: CallbackContext) -> bool:
        from_user = update.effective_message.from_user
        return from_user.username in self._config.TELEGRAM_ADMIN_USERNAMES.value


CONFIG_ADMINS = _ConfigAdmins()


class DeineMuddaBot:

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._antispam = AntiSpam(config, persistence)
        self._config = config
        self._persistence = persistence
        self._response_manager = ResponseManager(self._persistence)

        self._updater = Updater(token=self._config.TELEGRAM_BOT_TOKEN.value,
                                use_context=True)

        handler_groups = {
            0: [MessageHandler(filters=None, callback=self._any_message_callback)],
            1: [MessageHandler(
                filters=Filters.group & (~ Filters.reply) & (~ Filters.forwarded),
                callback=self._group_message_callback)],
            2: [CallbackQueryHandler(callback=self._inline_keyboard_click_callback)],
            3: [MessageHandler(Filters.text, callback=self._message_callback),
                CommandHandler(
                    COMMAND_COMMANDS,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._commands_command_callback),
                CommandHandler(
                    COMMAND_VERSION,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._version_command_callback),
                CommandHandler(
                    COMMAND_CONFIG,
                    filters=(~ Filters.forwarded) & (~ Filters.reply),
                    callback=self._config_command_callback),
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

    def _shout(self, bot: Bot, message, text: str, reply: bool = True, show_vote_menu: bool = True):
        """
        Shouts a message
        :param bot: the bot instance
        :param message: the message instance
        :param text: the text to shout
        :param reply: whether to reply to the original message
        :param show_vote_menu: whether to show a voting menu
        """
        shouting_text = "<b>{}!!!</b>".format(text.upper())

        reply_to_message_id = None
        if reply:
            reply_to_message_id = message.message_id

        menu_markup = None
        new_vote_menu_items = None
        if show_vote_menu and self._config.VOTING_ENABLED.value:
            new_vote_menu_items = [
                VoteMenuItem(id=VOTE_BUTTON_ID_THUMBS_UP, text=":thumbsup:"),
                VoteMenuItem(id=VOTE_BUTTON_ID_THUMBS_DOWN, text=":thumbsdown:")
            ]
            menu_markup = self._build_vote_menu(new_vote_menu_items)

        message = send_message(bot, message.chat_id,
                               message=shouting_text,
                               parse_mode=ParseMode.HTML,
                               reply_to=reply_to_message_id,
                               menu=menu_markup)

        if show_vote_menu and self._config.VOTING_ENABLED.value:
            # persist the vote menu with its id

            trigger_text = message.text

            # TODO: to be useful it would be necessary to know what the
            # initial message was that the bot responded to,
            # or more precisely, which response rule responded to the mentioned input
            # and what output it produced

            chat_entity = self._persistence.get_chat(message.chat_id)
            new_vote_menu = VoteMenu(chat_id=message.chat_id, message_id=message.message_id)
            new_vote_menu.items = new_vote_menu_items
            chat_entity.add_or_update_vote_menu(new_vote_menu)
            self._persistence.add_or_update_chat(chat_entity)

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
            chat = self._persistence.get_chat(chat_id)

        # remember chat user
        self._persistence.add_or_update_chat_member(chat, from_user)

    @staticmethod
    def _build_vote_menu(vote_menu_items: [VoteMenuItem]) -> InlineKeyboardMarkup:
        """
        Builds a vote menu from persistence items
        :param vote_menu_items: vote menu items
        :return: inline menu markup
        """
        vote_options = []
        for item in vote_menu_items:
            item_count = sum(list(map(lambda x: x.count, item.voters)))
            vote_options.append(("{} - {}".format(item.text, item_count), item.id))

        menu_markup = build_menu([vote_options])
        return menu_markup

    def _inline_keyboard_click_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        user_id = update.callback_query.from_user.id
        chat_id = update.effective_chat.id
        message_id = update.effective_message.message_id

        query = update.callback_query
        query_id = query.id
        selection_data = query.data

        try:
            chat_entity = self._persistence.get_chat(chat_id)
            if chat_entity is None:
                bot.answer_callback_query(query_id, text="Unknown message, cant vote")
                return
            vote_menu = chat_entity.get_vote_menu(message_id)
            if vote_menu is None:
                LOGGER.warning("Couldn't find vote menu for message: {}".format(message_id))
                bot.answer_callback_query(query_id, text="Unknown message, cant vote")
                return

            # register and persist vote (or revoke it)
            vote_menu.vote(user_id, selection_data)
            self._persistence.add_or_update_chat(chat_entity)

            # get new instance of persisted chat
            chat_entity = self._persistence.get_chat(chat_entity.id)
            vote_menu = chat_entity.get_vote_menu(message_id)
            self._response_manager.evaluate(chat_entity, vote_menu)

            menu_markup = self._build_vote_menu(vote_menu.items)

            query.edit_message_reply_markup(reply_markup=menu_markup)
            bot.answer_callback_query(query_id, text='Vote accepted')
        except Exception:
            logging.exception("Error processing vote")
            bot.answer_callback_query(query_id, text="Error counting vote")

    @MESSAGE_TIME.time()
    def _message_callback(self, update: Update, context: CallbackContext):
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

    @command(
        name=COMMAND_COMMANDS,
        description="List commands supported by this bot.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    def _commands_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        text = generate_command_list(update, context)
        send_message(bot, chat_id, text, parse_mode=ParseMode.MARKDOWN)

    @command(
        name=COMMAND_VERSION,
        description="Show application version.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    def _version_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id
        text = "Version: `{}`".format(DEINE_MUDDA_VERSION)
        send_message(bot, chat_id, text, parse_mode=ParseMode.MARKDOWN, reply_to=message_id)

    @command(
        name=COMMAND_CONFIG,
        description="Show current application configuration.",
        permissions=PRIVATE_CHAT & CONFIG_ADMINS
    )
    def _config_command_callback(self, update: Update, context: CallbackContext):
        from container_app_conf.formatter.toml import TomlFormatter

        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        text = self._config.print(formatter=TomlFormatter())
        text = "```\n{}\n```".format(text)
        send_message(bot, chat_id, text, parse_mode=ParseMode.MARKDOWN, reply_to=message_id)

    @command(
        name=COMMAND_STATS,
        description="List bot statistics.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    def _stats_command_callback(self, update: Update, context: CallbackContext) -> None:
        """
        /stats command handler
        :param update: the chat update object
        :param context: telegram context
        """
        bot = context.bot
        message_id = update.effective_message.message_id
        chat_id = update.effective_message.chat_id

        text = format_metrics()

        send_message(bot, chat_id, text, reply_to=message_id)

    @command(
        name=COMMAND_MUDDA,
        description="Trigger the bot manually.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    def _mudda_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        if self._antispam.process_message(update, context):
            return

        text = "deine mudda"
        self._shout(bot, update.message, text, reply=False, show_vote_menu=False)

    @command(
        name=COMMAND_GET_SETTINGS,
        description="Show settings for the current chat.",
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
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
            send_message(bot, chat_id, message, reply_to=message_id)
        else:
            # TODO: would be better if this could display default values to give at least some information
            send_message(bot, chat_id, "No chat specific settings set", reply_to=message_id)

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
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    def _set_chance_command_callback(self, update: Update, context: CallbackContext, probability):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting(SETTINGS_TRIGGER_PROBABILITY_KEY, str(probability))
        self._persistence.add_or_update_chat(chat)

        send_message(bot, chat_id, message="TriggerChance: {}%".format(probability * 100), reply_to=message_id)

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
        permissions=PRIVATE_CHAT | GROUP_CREATOR | GROUP_ADMIN | CONFIG_ADMINS
    )
    def _set_antispam_command_callback(self, update: Update, context: CallbackContext, state: str):
        bot = context.bot
        chat_id = update.effective_message.chat_id
        message_id = update.effective_message.message_id

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting(SETTINGS_ANTISPAM_ENABLED_KEY, state)
        self._persistence.add_or_update_chat(chat)

        send_message(bot, chat_id, message="Antispam: {}".format(state), reply_to=message_id)
