import datetime
import re
from random import randint

from pattern.text.de import parse, parsetree, pprint
from pattern.text.search import search
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# dictionary used for antispam-protection, if activated
spamtracker = {}

# dictionary used to store per-chat-settings
settings = {}

# dictionary used to store last message per chat
last_message = {}

# list used for collecting user names (as there is no member list yet)
known_names = set([])


def sendMessage(bot, message, text, reply=True):
    if reply:
        bot.sendMessage(
            chat_id=message.chat_id,
            reply_to_message_id=message.message_id,
            parse_mode='HTML',
            text='<b>' + text.upper() + '!!!</b>'
        )
    else:
        bot.sendMessage(
            chat_id=message.chat_id,
            parse_mode='HTML',
            text='<b>' + text.upper() + '!!!</b>'
        )


def reply(bot, update):
    # get trigger_chance-setting per chat
    chat_id = update.message.chat_id
    if chat_id not in settings:
        new_elem = {chat_id: [5, 'on']}
        settings.update(new_elem)
    TRIGGER_CHANCE = settings[chat_id][0]
    last_message.update({chat_id: update.message.text})

    # if user-name is new (as in: unknown to the bot), add it to known names
    name = update.message.from_user.first_name.upper()
    if name not in known_names:
        known_names.add(name)

    # print tags and chunks for debugging
    pprint(parse(update.message.text, relations=True, lemmata=True))

    # remove duplicate whitespaces from the message
    input = re.sub(' +', ' ', update.message.text)
    # remove all special characters from the message
    input = re.sub('[^A-Za-z0-9| |?]+', '', input)
    # we will only parse the message in lower case
    input = input.lower()

    print(input)

    # reflect counter intelligence
    hit = re.search(r"^dei(ne)? (mudda|mutter|mama)", input)
    if (hit): return sendMessage(bot, update.message, 'nee, ' + hit.group(0))

    # easter egg #1: spongebob
    if re.search(r"^wer wohnt in ner ananas ganz tief im meer?", input):
        return sendMessage(bot, update.message, 'spongebob schwammkopf')
    # easter egg #2: ricola / me
    elif re.search(r"^wer (hat es|hats) erfunden?", input):
        if (randint(0, 3) == 3):
            return sendMessage(bot, update.message, 'benjamin oesterle')
        else:
            return sendMessage(bot, update.message, 'ricola')
    # easter egg #3: ghostbusters
    elif re.search(r"^who y(ou|a) gonna call\?", input):
        return sendMessage(bot, update.message, 'ghostbusters')

    # german/english trigger for why questions
    if re.search(r"(^| )(warum|wieso|weshalb|weswegen|why)(| (.)+)\?", input):
        if (randint(0, 100) <= TRIGGER_CHANCE):
            return sendMessage(bot, update.message, 'sex')

    # adjective counter intelligence
    for match in search('ADJP', parsetree(update.message.text, relations=True)):
        if (randint(0, 100) <= TRIGGER_CHANCE):
            word = match.constituents()[-1].string
            print("Chunk to counter: " + word)
            if (randint(0, 3) == 3):
                user_id = randint(0, len(known_names) - 1)
                return sendMessage(bot, update.message, list(known_names)[user_id] + 's mudda is\' ' + word)
            else:
                return sendMessage(bot, update.message, 'deine mudda is\' ' + word)

    # german trigger for who questions
    if re.search(r"(^| )(irgend)?(wer|jemand)(| (.)+)\?", input):
        if (randint(0, 100) <= TRIGGER_CHANCE):
            if (randint(0, 3) == 3):
                user_id = randint(0, len(known_names) - 1)
                return sendMessage(bot, update.message, list(known_names)[user_id] + 's mudda')
            else:
                return sendMessage(bot, update.message, 'deine mudda')
    # english trigger for who questions
    elif re.search(r"who(| (.)+)\?", input):
        if (randint(0, 100) <= TRIGGER_CHANCE):
            sendMessage(bot, update.message, 'your momma')


def antispam(bot, update, n=30):
    chat_id = update.message.chat_id
    if chat_id not in settings:
        new_elem = {chat_id: [30, 'on']}
        settings.update(new_elem)
    TRIGGER_CHANCE = settings[chat_id][0]
    ANTISPAM = settings[chat_id][1]

    if (ANTISPAM == "off"):
        return True
    else:
        user_id = update.message.from_user.id
        now = datetime.datetime.now()

        if user_id in spamtracker:
            difference = now - spamtracker[user_id][0]
            if (difference < datetime.timedelta(seconds=n)):
                warned = spamtracker[user_id][1]
                if warned:
                    bot.sendMessage(update.message.chat_id,
                                    parse_mode='HTML',
                                    text=update.message.from_user.name + ': <b>See ya!</b>')
                    del spamtracker[user_id]
                    # print(spamtracker)
                    kicked = bot.kickChatMember(update.message.chat_id, user_id)
                    print('Kicked: ' + kicked)
                else:
                    bot.sendMessage(update.message.chat_id,
                                    parse_mode='HTML',
                                    text=update.message.from_user.name + ': <b>Stop spamming or I will kick you!</b>')
                    new_elem = {user_id: [now, True]}
                    spamtracker.update(new_elem)
                return False

        warned = False
        new_elem = {user_id: [now, warned]}
        spamtracker.update(new_elem)

        return True


def mudda(bot, update):
    no_spam = antispam(bot, update)

    if no_spam:
        chat_id = update.message.chat_id
        if chat_id in last_message:
            messageText = last_message[chat_id]
            for match in search('ADJP', parsetree(messageText, relations=True)):
                word = match.constituents()[-1].string
                print("Chunk to counter: " + word)
                if (randint(0, 3) == 3):
                    user_id = randint(0, len(known_names) - 1)
                    text = list(known_names)[user_id] + 's mudda is\' ' + word
                else:
                    text = 'deine mudda is\' ' + word
        else:
            text = 'deine mudda'

        sendMessage(bot, update.message, text, reply=False)


def set_antispam(bot, update, args):
    # only run if user is administrator/creator or it's a private chat
    chat_type = bot.getChat(update.message.chat_id).type
    member = bot.getChatMember(update.message.chat_id, update.message.from_user.id)
    if (chat_type == 'private' or member.status == "administrator" or member.status == "creator"):
        if args:
            # only run if there's only 1 argument
            if (len(args) > 1):
                bot.sendMessage(update.message.chat_id, text='set_antispam <on|off>')
                return

            # only run if argument is 'on' or 'off'
            if not (args[0] == "on" or args[0] == "off"):
                bot.sendMessage(update.message.chat_id, text='set_antispam <on|off>')
                return

            chat_id = update.message.chat_id
            bot.sendMessage(update.message.chat_id, text='Turn antispam ' + args[0])
            if chat_id in settings:
                TRIGGER_CHANCE = settings[chat_id][0]
                new_elem = {chat_id: [TRIGGER_CHANCE, args[0]]}
            else:
                new_elem = {chat_id: [30, args[0]]}
            settings.update(new_elem)
        else:
            bot.sendMessage(update.message.chat_id, text='set_antispam <on|off>')


def set_chance(bot, update, args):
    # only run if user is administrator/creator or it's a private chat
    chat_type = bot.getChat(update.message.chat_id).type
    member = bot.getChatMember(update.message.chat_id, update.message.from_user.id)
    if (chat_type == 'private' or member.status == "administrator" or member.status == "creator"):
        if args:
            # only run if there's only 1 argument
            if (len(args) > 1):
                bot.sendMessage(update.message.chat_id, text='set_chance <0-100>')
                return

            # only run if it's a number ...
            try:
                chance = int(args[0])
            except ValueError:
                bot.sendMessage(update.message.chat_id, text='set_chance <0-100>')
                return

            # ... and in valid range 0-100
            if (chance < 0 or chance > 100):
                bot.sendMessage(update.message.chat_id, text='set_chance <0-100>')
                return

            chat_id = update.message.chat_id
            bot.sendMessage(update.message.chat_id, text='Set trigger-chance ' + args[0])
            if chat_id in settings:
                ANTISPAM = settings[chat_id][1]
                new_elem = {chat_id: [chance, ANTISPAM]}
            else:
                new_elem = {chat_id: [chance, 'on']}
            settings.update(new_elem)
        else:
            bot.sendMessage(update.message.chat_id, text='set_chance <0-100>')


# Token for the deineMuddaBot
updater = Updater('qwertz')

# Token for the devMumBot
# updater = Updater('qwerty')

updater.dispatcher.add_handler(MessageHandler([Filters.text], reply))

# user commands
updater.dispatcher.add_handler(CommandHandler('mudda', mudda))

# admin commands
updater.dispatcher.add_handler(CommandHandler('set_antispam', set_antispam, pass_args=True))
updater.dispatcher.add_handler(CommandHandler('set_chance', set_chance, pass_args=True))

updater.start_polling(clean=True)
updater.idle()
