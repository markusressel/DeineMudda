import re
from random import randint

from deinemudda.response.rule import ResponseRule


class WhoGermanRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Respond to 'who' questions in german"

    def matches(self, message: str):
        return re.search(r"(^| )(irgend)?(wer|jemand)(| (.)+)\?", message)

    def get_response(self, sender: str, message: str):
        if randint(0, 3) == 3:
            # TODO: get random names from the chat of the sender
            # known_names = self._persistence.get_names(chat.id)
            # user_id = randint(0, len(known_names) - 1)

            username = sender
            return "{}'s mudda".format(username)
        else:
            return 'deine mudda'


class WhoEnglishRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Respond to 'who' questions in english"

    def matches(self, message: str):
        return re.search(r"who(| (.)+)\?", message)

    def get_response(self, sender: str, message: str):
        return 'your momma'


class WhyRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Respond to 'why' questions"

    def matches(self, message: str):
        return re.search(r"(^| )(warum|wieso|weshalb|weswegen|why)(| (.)+)\?", message)

    def get_response(self, sender: str, message: str):
        return 'sex'
