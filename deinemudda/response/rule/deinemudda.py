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
from typing import List, Tuple

from deinemudda.persistence import Chat
from deinemudda.response.rule import ResponseRule


class GenitiveFirstRule(ResponseRule):
    __description__ = "Respond to 'wen' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(wen)(\?| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return f"{user.first_name}'s mudda"
        else:
            return 'deine mudda'


class GenitiveSecondRule(ResponseRule):
    __description__ = "Respond to 'wessen' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(wessen)(| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return f"von {user.first_name}'s mudda"
        else:
            return 'von deiner mudda'


class DativRule(ResponseRule):
    __description__ = "Respond to 'wem' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(wem)(| (.)+)", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return f"{user.first_name}'s mudda"
        else:
            return 'deiner mudda'


class WhoGermanRule(ResponseRule):
    __description__ = "Respond to 'who' questions in german"

    def matches(self, message: str) -> bool:
        return re.search(r"(^| )(irgend)?(wer|jemand)(| (.)+)\?", message, re.IGNORECASE) is not None

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        if randint(0, 3) == 3:
            user = choice(chat.users)
            return f"{user.first_name}'s mudda"
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
        return f"nee, {hit.group(0)}"


class CustomWordAdjectiveRule(ResponseRule):
    __description__ = "Custom adjective words"

    words = [
        "geil",
        "saugeil",
    ]

    def matches(self, message: str) -> bool:
        return any(map(lambda x: re.search(rf"(^| ){x}( |$)", message, re.IGNORECASE) is not None, self.words))

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        contained_words = self._find_matches(message)

        dice = randint(0, 2)

        if dice == 0:
            user = choice(chat.users)
            return f"{user.first_name}'s mudda is' {' und '.join(contained_words)}"
        elif dice == 1:
            return "wie deine mudda beim kacken"
        else:
            return f"deine mudda is' {' und '.join(contained_words)}"

    def _find_matches(self, message) -> List[str]:
        return list(
            filter(
                lambda x: re.search(rf"(^| ){x}( |$)", message, re.IGNORECASE) is not None,
                self.words
            )
        )


class CustomWordNounRule(ResponseRule):
    __description__ = "Custom noun words"

    words = [
        ("kacknase", "ne"),
    ]

    def matches(self, message: str) -> bool:
        return any(map(lambda x: x[0].lower() in message.lower(), self.words))

    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        contained_words = self._find_matches(message)

        suffix = ' und '.join(list(map(lambda x: f"{x[1]} {x[0]}", contained_words)))

        dice = randint(0, 1)

        if dice == 0:
            user = choice(chat.users)
            return f"{user.first_name}'s mudda is' {suffix}"
        else:
            return f"deine mudda is' {suffix}"

    def _find_matches(self, message) -> List[Tuple[str, str]]:
        return list(filter(lambda x: x[0].lower() in message.lower(), self.words))


class AdjectiveCounterIntelligenceRule(ResponseRule):
    __description__ = "Adjective counter intelligence"

    match_cache = {}

    def matches(self, message: str) -> bool:

        if hash(message) in self.match_cache:
            return True

        constituents = self._find_adpj(message)
        if len(constituents) > 0 and constituents[-1].lower() not in [
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

            # cache result
            self.match_cache[hash(message)] = constituents
            return True
        else:
            return False

    def get_response(self, chat: Chat, sender: int, message: str) -> str or None:
        if hash(message) in self.match_cache:
            matches = self.match_cache[hash(message)]
        else:
            matches = self._find_adpj(message)

        dice = randint(0, 2)

        word_response = " ".join(matches)

        if dice == 0:
            user = choice(chat.users)
            return f"{user.first_name}'s mudda is' {word_response}"
        elif dice == 1:
            return "wie deine mudda beim kacken"
        else:
            return f"deine mudda is' {word_response}"

    def _find_adpj(self, message) -> List[str]:
        from textblob_de import TextBlobDE as TextBlob
        blob = TextBlob(message)
        parsed = blob.parse()

        result = self._extract_adjp(parsed)
        if result is None:
            result = []

        return result

    def _extract_adjp(self, parsed):
        result = []
        sentences = parsed.split()
        for sentence in sentences:
            for word_tuple in sentence:
                word = word_tuple[0]
                if any(map(lambda x: "ADJP" in x, word_tuple[1:])):
                    result.append(word)

        if len(result) <= 0:
            return None
        else:
            return result

    def _extract_np(self, parsed):
        result = []
        sentences = parsed.split()
        for sentence in sentences:
            for word_tuple in sentence:
                word = word_tuple[0]
                if any(map(lambda x: "-NP" in x, word_tuple[1:])):
                    result.append(word)
        return result
