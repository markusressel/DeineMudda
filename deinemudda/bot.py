import datetime
import logging

from telegram import Bot, Update, ParseMode
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, CallbackContext

from deinemudda.config import AppConfig
from deinemudda.const import COMMAND_MUDDA, COMMAND_SET_ANTISPAM, COMMAND_SET_CHANCE, COMMAND_COMMANDS
from deinemudda.persistence import Persistence, User, Chat
from deinemudda.response import ResponseManager
from deinemudda.telegram_command import command, generate_command_list
from deinemudda.telegram_command.argument import CommandArgument
from deinemudda.util import send_message

# dictionary used for antispam-protection, if activated
spamtracker = {}

# dictionary used to store last message per chat
last_message = {}

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
            1: [MessageHandler(Filters.text, self._message_callback),
                CommandHandler(COMMAND_COMMANDS, self._commands_command_callback),
                CommandHandler(COMMAND_MUDDA, self._mudda_command_callback),
                CommandHandler(COMMAND_SET_ANTISPAM, self._set_antispam_command_callback, pass_args=True),
                CommandHandler(COMMAND_SET_CHANCE, self._set_chance_command_callback, pass_args=True)],
            2: [MessageHandler(Filters.group & (~ Filters.reply), self._group_message_callback)]
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

    def _message_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.message.chat_id
        last_message.update({chat_id: update.message.text})

        from_user = update.message.from_user
        chat = self._persistence.get_chat(chat_id)

        response_message = self._response_manager.process_message(chat, from_user.first_name, update.message.text)
        if response_message:
            self._shout(bot, update.message, response_message)

    def _group_message_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.message.chat_id
        chat_type = update.effective_chat.type

        my_id = bot.get_me().id

        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == my_id:
                    LOGGER.debug("Bot was added to group: {}".format(chat_id))
                    chat_entity = Chat(id=chat_id, type=chat_type)
                    self._persistence.add_or_update_chat(chat_entity)
                else:
                    LOGGER.debug("{} ({}) joined group {}".format(member.full_name, member.id, chat_id))
                    chat = self._persistence.get_chat(chat_id)
                    user_entity = User(
                        id=member.id,
                        first_name=member.first_name,
                        full_name=member.full_name,
                        username=member.username
                    )
                    chat.users.append(user_entity)
                    self._persistence.add_or_update_chat(chat)

        if update.message.left_chat_member:
            member = update.message.left_chat_member
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
        chat_id = update.message.chat_id

        chat = self._persistence.get_chat(chat_id)
        if chat is None:
            return
        anti_spam = chat.get_setting("antispam", "on")

        if anti_spam == "off":
            return False

        user_id = update.message.from_user.id
        now = datetime.datetime.now()

        if user_id in spamtracker:
            difference = now - spamtracker[user_id][0]
            if difference < datetime.timedelta(seconds=n):
                warned = spamtracker[user_id][1]
                if warned:
                    send_message(bot,
                                 update.message.chat_id,
                                 parse_mode="HTML",
                                 message="{}: <b>See ya!</b>".format(update.message.from_user.name))
                    del spamtracker[user_id]
                    # print(spamtracker)
                    kicked = bot.kickChatMember(update.message.chat_id, user_id)
                    LOGGER.debug("Kicked: {}".format(kicked))
                else:
                    send_message(bot,
                                 update.message.chat_id,
                                 parse_mode="HTML",
                                 message="{}: <b>Stop spamming or I will kick you!</b>".format(
                                     update.message.from_user.name))
                    new_elem = {user_id: [now, True]}
                    spamtracker.update(new_elem)
                return True

        warned = False
        new_elem = {user_id: [now, warned]}
        spamtracker.update(new_elem)

        return False

    @command(
        name="commands",
        description="List commands supported by this bot."
    )
    def _commands_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.message.chat_id
        text = generate_command_list()
        send_message(bot, chat_id, text, parse_mode=ParseMode.MARKDOWN)

    @command(
        name="mudda",
        description="Trigger the bot manually."
    )
    def _mudda_command_callback(self, update: Update, context: CallbackContext):
        bot = context.bot
        chat_id = update.message.chat_id
        message_id = update.message.message_id

        if self._antispam(update, context):
            LOGGER.debug("Removing message because of spam")
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            return

        text = "deine mudda"
        self._shout(bot, update.message, text, reply=False)

    @command(
        name="set_chance",
        description="Set the trigger probability to a specific value.",
        arguments=[
            CommandArgument(
                name="probability",
                example="0.13",
                type=float,
                converter=lambda x: float(x),
                description="The probability to set",
                validator=lambda x: 0 <= x <= 1
            )
        ]
    )
    def _set_chance_command_callback(self, update: Update, context: CallbackContext, probability):
        bot = context.bot
        chat_id = update.message.chat_id
        from_user = update.message.from_user

        chat_type = update.effective_chat.type
        member = bot.getChatMember(chat_id, from_user.id)

        # only run if user is administrator/creator or it's a private chat
        if chat_type == 'private' or member.status == "administrator" or member.status == "creator":
            # TODO: use permission decorator for this
            pass
        else:
            return

        try:

            # ... and in valid range 0-100
            if probability < 0 or probability > 1:
                raise ValueError("Illegal propability value")
        except ValueError:
            send_message(bot, chat_id, message="Usage: set_chance <0.00-1.00>")
            return

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting("TriggerChance", str(probability))
        self._persistence.add_or_update_chat(chat)

        send_message(bot, chat_id, message="TriggerChance: {}%".format(probability * 100))

    @command(
        name="set_antispam",
        description="Turn antispam feature on/off",
        arguments=[
            CommandArgument(
                name="state",
                example="on",
                description="The new state",
                validator=lambda x: x in ["on", "off"]
            )
        ]
    )
    def _set_antispam_command_callback(self, update: Update, context: CallbackContext, new_state: str):
        # only run if user is administrator/creator or it's a private chat
        bot = context.bot
        chat_id = update.message.chat_id
        from_user = update.message.from_user
        chat_type = update.effective_chat.type

        member = bot.getChatMember(chat_id, from_user.id)
        if chat_type == 'private' or member.status == "administrator" or member.status == "creator":
            # TODO: use permission decorator for this
            pass
        else:
            return

        chat = self._persistence.get_chat(chat_id)
        chat.set_setting("antispam", new_state)
        self._persistence.add_or_update_chat(chat)

        send_message(bot, chat_id, message="Antispam: {}".format(new_state))
