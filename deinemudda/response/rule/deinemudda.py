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

import re
from random import randint, choice

from deinemudda.persistence import Chat
from deinemudda.response.rule import ResponseRule


class GenitiveFirstRule(ResponseRule):
    __description__ = "Respond to 'wen' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(wen)(\?| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return "{}'s mudda".format(user.first_name)
        else:
            return 'deine mudda'


class GenitiveSecondRule(ResponseRule):
    __description__ = "Respond to 'wessen' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(wessen)(| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return "von {}'s mudda".format(user.first_name)
        else:
            return 'von deiner mudda'


class DativRule(ResponseRule):
    __description__ = "Respond to 'wem' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(wem)(| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return "{}'s mudda".format(user.first_name)
        else:
            return 'deiner mudda'


class WhoGermanRule(ResponseRule):
    __description__ = "Respond to 'who' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(irgend)?(wer|jemand)(| (.)+)\?", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return "{}'s mudda".format(user.first_name)
        else:
            return 'deine mudda'


class WhoEnglishRule(ResponseRule):
    __description__ = "Respond to 'who' questions in english"

    def matches(self, message: str) -> bool:
        return re.search(r"who(| (.)+)\?", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        return 'your momma'


class WhyRule(ResponseRule):
    __description__ = "Respond to 'why' questions"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(warum|wieso|weshalb|weswegen|why)(| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        return 'sex'


class ReflectCounterIntelligenceRule(ResponseRule):
    __description__ = "Respond to messages containing phrases similar to 'your mother'"

    regex = r"^dei(ne)? (mudda|mutter|mama)"

    def matches(self, message: str) -> bool:
        return re.search(self.regex, message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        hit = re.search(self.regex, message, re.IGNORECASE)
        return "nee, {}".format(hit.group(0))


class AdjectiveCounterIntelligenceRule(ResponseRule):
    __description__ = "Adjective counter intelligence"

    match_cache = {}

    def matches(self, message: str) -> bool:
        from pattern.text.search import search
        from pattern.text.de import parsetree

        if hash(message) in self.match_cache:
            return True

        message_tree = parsetree(message, relations=True)
        matches = search('ADJP', message_tree)
        if len(matches) > 0:
            if matches[0].constituents()[-1].string.lower() in [
                "vermutlich",
                "selbe",
                "gute",
                "lieber",
                "eigentlich",
                "jam",
                "neues",
                "leid",
                "gleich",
                "du"
            ]:
                return False

            # cache result
            self.match_cache[hash(message)] = matches
            return True
        else:
            return False

    def get_response(self, chat: Chat, sender: int, message: str) -> str or None:
        if hash(message) in self.match_cache:
            matches = self.match_cache[hash(message)]
        else:
            from pattern.text.search import search
            from pattern.text.de import parsetree
            message_tree = parsetree(message, relations=True)
            matches = search('ADJP', message_tree)

        for match in matches:
            word = match.constituents()[-1].string

            dice = randint(0, 2)

            if dice == 0:
                user = choice(chat.users)
                return "{}'s mudda is' {}".format(user.first_name, word)
            elif dice == 1:
                return "wie deine mudda beim kacken"
            else:
                return "deine mudda is' {}".format(word)
