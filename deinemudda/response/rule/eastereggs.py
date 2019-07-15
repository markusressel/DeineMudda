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
from random import randint

from deinemudda.persistence import Chat
from deinemudda.response.rule import ResponseRule


class SpongebobRule(ResponseRule):
    __id__ = "SpongebobRule"
    __description__ = "Spongebob easter egg"
    __priority__ = 100.0

    def matches(self, message: str):
        return re.search(r"^wer wohnt in ner ananas ganz tief im meer", message, re.IGNORECASE)

    def get_response(self, chat: Chat, sender: str, message: str):
        return 'spongebob schwammkopf'


class RicolaRule(ResponseRule):
    __id__ = "RicolaRule"
    __description__ = "Ricola easter egg"
    __priority__ = 100.0

    def matches(self, message: str):
        return re.search(r"^wer (hat es|hats) erfunden", message, re.IGNORECASE)

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
        return re.search(r"^who y(ou|a) gonna call", message, re.IGNORECASE)

    def get_response(self, chat: Chat, sender: str, message: str):
        return 'ghostbusters'
