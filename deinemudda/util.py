from telegram import Bot


def send_message(bot: Bot, chat_id: str, message: str, parse_mode: str = None, reply_to: int = None):
    """
    Sends a text message to the given chat
    :param bot: the bot
    :param chat_id: the chat id to send the message to
    :param message: the message to chat (may contain emoji aliases)
    :param parse_mode: specify whether to parse the text as markdown or HTML
    :param reply_to: the message id to reply to
    """
    from emoji import emojize

    emojized_text = emojize(message, use_aliases=True)
    bot.send_message(chat_id=chat_id, parse_mode=parse_mode, text=emojized_text, reply_to_message_id=reply_to)
