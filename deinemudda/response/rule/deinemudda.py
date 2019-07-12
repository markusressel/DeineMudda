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


class ReflectCounterIntelligenceRule(ResponseRule):
    regex = r"^dei(ne)? (mudda|mutter|mama)"

    @property
    def description(self) -> str:
        return "Respond to messages containing phrases similar to 'your mother'"

    def matches(self, message: str):
        return re.search(self.regex, message)

    def get_response(self, sender: str, message: str):
        hit = re.search(self.regex, message)
        return "nee, {}".format(hit.group(0))


class AdjectiveCounterIntelligenceRule(ResponseRule):

    @property
    def description(self) -> str:
        return "Adjective counter intelligence"

    def matches(self, message: str):
        # we need to do the parsetreecalculation anyway so
        # there is no need to check this first
        return True

    def get_response(self, sender: str, message: str):
        from pattern.text.search import search
        from pattern.text.de import parsetree
        for match in search('ADJP', parsetree(message, relations=True)):
            word = match.constituents()[-1].string

            if randint(0, 3) == 3:
                # TODO: get random names from the chat of the sender
                # known_names = self._persistence.get_names(chat.id)
                # user_id = randint(0, len(known_names) - 1)

                username = sender
                return "{}'s mudda is\' {}".format(username, word)
            else:
                return "deine mudda is\' {}".format(word)
