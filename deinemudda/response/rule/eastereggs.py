import re
from random import randint

from deinemudda.response.rule import ResponseRule


class SpongebobRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Spongebob easter egg"

    def matches(self, message: str):
        return re.search(r"^wer wohnt in ner ananas ganz tief im meer?", message)

    def get_response(self, sender: str, message: str):
        return 'spongebob schwammkopf'


class RicolaRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Ricola easter egg"

    def matches(self, message: str):
        return re.search(r"^wer (hat es|hats) erfunden?", message)

    def get_response(self, sender: str, message: str):
        if randint(0, 3) == 3:
            return 'benjamin oesterle'
        else:
            return 'ricola'


class GhostbustersRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Ghostbusters easter egg"

    def matches(self, message: str):
        return re.search(r"^who y(ou|a) gonna call\?", message)

    def get_response(self, sender: str, message: str):
        return 'ghostbusters'
