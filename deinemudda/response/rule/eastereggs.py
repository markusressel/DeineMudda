import re
from random import randint

from deinemudda.persistence import Chat
from deinemudda.response.rule import ResponseRule


class SpongebobRule(ResponseRule):
    __id__ = "SpongebobRule"
    __description__ = "Spongebob easter egg"
    __priority__ = 100.0

    def matches(self, message: str):
        return re.search(r"^wer wohnt in ner ananas ganz tief im meer\?", message, re.IGNORECASE)

    def get_response(self, chat: Chat, sender: str, message: str):
        return 'spongebob schwammkopf'


class RicolaRule(ResponseRule):
    __id__ = "RicolaRule"
    __description__ = "Ricola easter egg"
    __priority__ = 100.0

    def matches(self, message: str):
        return re.search(r"^wer (hat es|hats) erfunden\?", message, re.IGNORECASE)

    def get_response(self, chat: Chat, sender: str, message: str):
        if randint(0, 3) == 3:
            return 'benjamin oesterle'
        else:
            return 'ricola'


class GhostbustersRule(ResponseRule):
    __id__ = "GhostbustersRule"
    __description__ = "Ghostbusters easter egg"
    __priority__ = 100.0

    def matches(self, message: str):
        return re.search(r"^who y(ou|a) gonna call\?", message, re.IGNORECASE)

    def get_response(self, chat: Chat, sender: str, message: str):
        return 'ghostbusters'
