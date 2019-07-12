import datetime
from random import randint

from pattern.text.de import parsetree, parse
from pattern.text.search import search
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler

from deinemudda.config import AppConfig
from deinemudda.const import COMMAND_MUDDA, COMMAND_SET_ANTISPAM, COMMAND_SET_CHANCE
from deinemudda.persistence import Persistence
from deinemudda.response import ResponseManager
from deinemudda.util import send_message

# dictionary used for antispam-protection, if activated
spamtracker = {}

# dictionary used to store per-chat-settings
settings = {}

# dictionary used to store last message per chat
last_message = {}

# list used for collecting user names (as there is no member list yet)
known_names = set([])


class DeineMuddaBot:

    def __init__(self, config: AppConfig, persistence: Persistence):
        self._config = config
        self._persistence = persistence
        self._response_manager = ResponseManager(self._persistence)

        # self._updater = Updater(token=self._config.TELEGRAM_BOT_TOKEN.value, use_context=True)
        self._updater = Updater(token=self._config.TELEGRAM_BOT_TOKEN.value)
        self._updater.dispatcher.add_handler(
            MessageHandler(filters=Filters.text, callback=self._reply))

        command_handlers = [
            CommandHandler(COMMAND_MUDDA, self._mudda),
            CommandHandler(COMMAND_SET_ANTISPAM, self._set_antispam, pass_args=True),
            CommandHandler(COMMAND_SET_CHANCE, self._set_chance, pass_args=True)
        ]

        for handler in command_handlers:
            self._updater.dispatcher.add_handler(handler)

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

    def _reply(self, bot, update):
        # get trigger_chance-setting per chat
        # TODO: get this from persistence
        chat_id = update.message.chat_id
        if chat_id not in settings:
            new_elem = {chat_id: [5, 'on']}
            settings.update(new_elem)
        trigger_chance = settings[chat_id][0]
        last_message.update({chat_id: update.message.text})

        # if user-name is new (as in: unknown to the bot), add it to known names
        # TODO: add this to persistence(?)
        name = update.message.from_user.first_name.upper()
        if name not in known_names:
            known_names.add(name)

        # print tags and chunks for debugging
        # TODO: use logger for this and don't log in production at all
        # pprint()
        parsed = parse(update.message.text, relations=True, lemmata=True)

        response_message = self._response_manager.process_message(name, update.message.text)
        if response_message:
            self._shout(bot, update.message, response_message)

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
                        print('Kicked: ' + kicked)
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

    def _mudda(self, bot, update):
        no_spam = self._antispam(bot, update)

        if no_spam:
            chat_id = update.message.chat_id
            if chat_id in last_message:
                message_text = last_message[chat_id]
                for match in search('ADJP', parsetree(message_text, relations=True)):
                    word = match.constituents()[-1].string
                    print("Chunk to counter: " + word)
                    if randint(0, 3) == 3:
                        user_id = randint(0, len(known_names) - 1)
                        text = list(known_names)[user_id] + 's mudda is\' ' + word
                    else:
                        text = 'deine mudda is\' ' + word
            else:
                text = 'deine mudda'

            self._shout(bot, update.message, text, reply=False)

    def _set_antispam(self, bot, update, args):
        # only run if user is administrator/creator or it's a private chat
        chat_type = bot.getChat(update.message.chat_id).type
        member = bot.getChatMember(update.message.chat_id, update.message.from_user.id)
        if chat_type == 'private' or member.status == "administrator" or member.status == "creator":
            if args:
                # only run if there's only 1 argument
                if len(args) > 1:
                    bot.send_message(update.message.chat_id, text='set_antispam <on|off>')
                    return

                # only run if argument is 'on' or 'off'
                if not (args[0] == "on" or args[0] == "off"):
                    bot.send_message(update.message.chat_id, text='set_antispam <on|off>')
                    return

                chat_id = update.message.chat_id
                bot.send_message(update.message.chat_id, text='Turn antispam ' + args[0])
                if chat_id in settings:
                    trigger_chance = settings[chat_id][0]
                    new_elem = {chat_id: [trigger_chance, args[0]]}
                else:
                    new_elem = {chat_id: [30, args[0]]}
                settings.update(new_elem)
            else:
                bot.send_message(update.message.chat_id, text='set_antispam <on|off>')

    def _set_chance(self, bot, update, args):
        # only run if user is administrator/creator or it's a private chat
        chat_type = bot.getChat(update.message.chat_id).type
        member = bot.getChatMember(update.message.chat_id, update.message.from_user.id)
        if chat_type == 'private' or member.status == "administrator" or member.status == "creator":
            if args:
                # only run if there's only 1 argument
                if len(args) > 1:
                    bot.send_message(update.message.chat_id, text='set_chance <0-100>')
                    return

                # only run if it's a number ...
                try:
                    chance = int(args[0])
                except ValueError:
                    bot.send_message(update.message.chat_id, text='set_chance <0-100>')
                    return

                # ... and in valid range 0-100
                if chance < 0 or chance > 100:
                    bot.send_message(update.message.chat_id, text='set_chance <0-100>')
                    return

                chat_id = update.message.chat_id
                bot.send_message(update.message.chat_id, text='Set trigger-chance ' + args[0])
                if chat_id in settings:
                    anti_spam = settings[chat_id][1]
                    new_elem = {chat_id: [chance, anti_spam]}
                else:
                    new_elem = {chat_id: [chance, 'on']}
                settings.update(new_elem)
            else:
                bot.send_message(update.message.chat_id, text='set_chance <0-100>')
