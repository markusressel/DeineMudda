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


class GenitiveRule(ResponseRule):
    __id__ = "GenitiveRule"
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
    __id__ = "DativRule"
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
    __id__ = "WhoGermanRule"
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
    __id__ = "WhoEnglishRule"
    __description__ = "Respond to 'who' questions in english"

    def matches(self, message: str) -> bool:
        return re.search(r"who(| (.)+)\?", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        return 'your momma'


class WhyRule(ResponseRule):
    __id__ = "WhyRule"
    __description__ = "Respond to 'why' questions"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(warum|wieso|weshalb|weswegen|why)(| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        return 'sex'


class ReflectCounterIntelligenceRule(ResponseRule):
    __id__ = "ReflectCounterIntelligenceRule"
    __description__ = "Respond to messages containing phrases similar to 'your mother'"

    regex = r"^dei(ne)? (mudda|mutter|mama)"

    def matches(self, message: str) -> bool:
        return re.search(self.regex, message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        hit = re.search(self.regex, message, re.IGNORECASE)
        return "nee, {}".format(hit.group(0))


class AdjectiveCounterIntelligenceRule(ResponseRule):
    __id__ = "AdjectiveCounterIntelligenceRule"
    __description__ = "Adjective counter intelligence"

    def matches(self, message: str) -> bool:
        # we need to do the parsetreecalculation anyway so
        # there is no need to check this first
        return True

    def get_response(self, chat: Chat, sender: int, message: str) -> str or None:
        from pattern.text.search import search
        from pattern.text.de import parsetree
        message_tree = parsetree(message, relations=True)
        for match in search('ADJP', message_tree):
            word = match.constituents()[-1].string

            dice = randint(0, 2)

            if dice == 0:
                user = choice(chat.users)
                return "{}'s mudda is' {}".format(user.first_name, word)
            elif dice == 1:
                return "wie deine mudda beim kacken"
            else:
                return "deine mudda is' {}".format(word)
