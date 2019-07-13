import datetime
import logging
from random import randint, choice

from pattern.text.de import parsetree
from pattern.text.search import search
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

from deinemudda.config import AppConfig
from deinemudda.const import COMMAND_MUDDA, COMMAND_SET_ANTISPAM, COMMAND_SET_CHANCE
from deinemudda.persistence import Persistence, User, Chat
from deinemudda.response import ResponseManager
from deinemudda.util import send_message

# dictionary used for antispam-protection, if activated
spamtracker = {}

# dictionary used to store per-chat-settings
settings = {}

# dictionary used to store last message per chat
last_message = {}

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class DeineMuddaBot:

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._config = config
        self._persistence = persistence
        self._response_manager = ResponseManager(self._persistence)

        # self._updater = Updater(token=self._config.TELEGRAM_BOT_TOKEN.value, use_context=True)
        self._updater = Updater(token=self._config.TELEGRAM_BOT_TOKEN.value)

        handler_groups = {
            1: [MessageHandler(Filters.text, self._message_callback),
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

    def _shout(self, bot, message, text: str, reply: bool = True):
        shouting_text = "<b>{}!!!</b>".format(text.upper())

        reply_to_message_id = None
        if reply:
            reply_to_message_id = message.message_id

        send_message(bot, message.chat_id,
                     message=shouting_text,
                     parse_mode='HTML',
                     reply_to=reply_to_message_id)

    def _message_callback(self, bot, update):
        # get trigger_chance-setting per chat
        # TODO: get this from persistence
        chat_id = update.message.chat_id
        if chat_id not in settings:
            new_elem = {chat_id: [5, 'on']}
            settings.update(new_elem)
        trigger_chance = settings[chat_id][0]
        last_message.update({chat_id: update.message.text})

        from_user = update.message.from_user
        chat = self._persistence.get_chat(chat_id)

        response_message = self._response_manager.process_message(chat, from_user.first_name, update.message.text)
        if response_message:
            self._shout(bot, update.message, response_message)

    def _group_message_callback(self, bot, update):
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
                chat.users = filter(lambda x: x.id != member.id, chat.users)
                self._persistence.add_or_update_chat(chat)

    def _antispam(self, bot, update, n=30):
        chat_id = update.message.chat_id
        if chat_id not in settings:
            new_elem = {chat_id: [30, 'on']}
            settings.update(new_elem)
        trigger_chance = settings[chat_id][0]
        anti_spam = settings[chat_id][1]

        if anti_spam == "off":
            return True
        else:
            user_id = update.message.from_user.id
            now = datetime.datetime.now()

            if user_id in spamtracker:
                difference = now - spamtracker[user_id][0]
                if difference < datetime.timedelta(seconds=n):
                    warned = spamtracker[user_id][1]
                    if warned:
                        bot.send_message(update.message.chat_id,
                                         parse_mode='HTML',
                                         text='{}: <b>See ya!</b>'.format(update.message.from_user.name))
                        del spamtracker[user_id]
                        # print(spamtracker)
                        kicked = bot.kickChatMember(update.message.chat_id, user_id)
                        LOGGER.debug("Kicked: {}".format(kicked))
                    else:
                        bot.send_message(update.message.chat_id,
                                         parse_mode='HTML',
                                         text='{}: <b>Stop spamming or I will kick you!</b>'.format(
                                             update.message.from_user.name))
                        new_elem = {user_id: [now, True]}
                        spamtracker.update(new_elem)
                    return False

            warned = False
            new_elem = {user_id: [now, warned]}
            spamtracker.update(new_elem)

            return True

    def _mudda_command_callback(self, bot, update):
        chat_id = update.message.chat_id

        no_spam = self._antispam(bot, update)
        if not no_spam:
            return

        text = "deine mudda"
        if chat_id in last_message:
            message_text = last_message[chat_id]
            for match in search('ADJP', parsetree(message_text, relations=True)):
                word = match.constituents()[-1].string
                LOGGER.debug("Chunk to counter: " + word)
                if randint(0, 3) == 3:
                    chat = self._persistence.get_chat(chat_id)
                    user = choice(chat.users)

                    text = "{}s mudda is' {}".format(user.first_name, word)
                else:
                    text = "deine mudda is' {}".format(word)

        self._shout(bot, update.message, text, reply=False)

    def _set_antispam_command_callback(self, bot, update, args):
        # only run if user is administrator/creator or it's a private chat
        chat_id = update.message.chat_id
        from_user = update.message.from_user
        chat_type = update.effective_chat.type

        member = bot.getChatMember(chat_id, from_user.id)
        if chat_type == 'private' or member.status == "administrator" or member.status == "creator":
            # TODO: use permission decorator for this
            pass
        else:
            return

        try:
            if not args:
                raise ValueError("Missing args")

            if len(args) > 1:
                raise ValueError("Invalid argument count: {}".format(args))

            new_value = args[0]
            # only run if argument is 'on' or 'off'
            if new_value not in ["on", "off"]:
                raise ValueError("Invalid argument")

            chat_id = update.message.chat_id
            bot.send_message(update.message.chat_id, text='Turn antispam ' + args[0])
            if chat_id in settings:
                trigger_chance = settings[chat_id][0]
                new_elem = {chat_id: [trigger_chance, args[0]]}
            else:
                new_elem = {chat_id: [30, args[0]]}
            settings.update(new_elem)
        except ValueError:
            bot.send_message(update.message.chat_id, text='set_antispam <on|off>')
            return

    def _set_chance_command_callback(self, bot, update, args):
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
            if not args:
                raise ValueError("Missing args")

            # only run if there's only 1 argument
            if len(args) > 1:
                raise ValueError("Invalid argument count: {}".format(args))

            chance = int(args[0])

            # ... and in valid range 0-100
            if chance < 0 or chance > 100:
                raise ValueError("Illegal propability value")
        except ValueError:
            send_message(bot, chat_id, message="set_chance <0-100>")
            return

        bot.send_message(chat_id, text='Set trigger-chance ' + args[0])
        if chat_id in settings:
            anti_spam = settings[chat_id][1]
            new_elem = {chat_id: [chance, anti_spam]}
        else:
            new_elem = {chat_id: [chance, 'on']}
        settings.update(new_elem)
