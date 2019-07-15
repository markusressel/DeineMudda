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

import logging
import re
from random import random

from deinemudda import util
from deinemudda.persistence import Persistence, Chat
from deinemudda.response.rule import ResponseRule
from deinemudda.stats import RESPONSES_COUNT

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


class ResponseManager:
    """
    Manages response rules
    """

    def __init__(self, persistence: Persistence):
        self._persistence: Persistence = persistence
        self.response_rules: [ResponseRule] = self._find_rules()

    def _find_rules(self):
        """
        :return: list of rules
        """
        from deinemudda.response import rule
        rule_classes = util.find_implementations(ResponseRule, rule)
        # construct implementations
        rule_instances = list(map(lambda x: x(self._persistence), rule_classes))
        return sorted(rule_instances, key=lambda x: x.__priority__, reverse=True)

    def find_matching_rule(self, chat: Chat, sender: str, message: str) -> ResponseRule or None:
        """
        Processes the given message and returns a response if one of the response rules match
        :param chat: the chat this message was sent in
        :param sender: the message sender
        :param message: the message
        :return: Response message or None
        """
        normalized_message = self._normalize(message)

        # print tags and chunks for debugging
        # TODO: use logger for this and don't log in production at all
        # pprint()
        from pattern import text
        parsed = text.parse(normalized_message, relations=True, lemmata=True)

        for response_rule in self.response_rules:
            # TODO: get trigger chance for specific rule based on chat id
            # trigger_chance = int(chat.get_setting("{}-TriggerChance".format(response_rule.__id__), default="1"))
            trigger_chance = float(chat.get_setting("TriggerChance", default="1"))

            if random() >= trigger_chance:
                # skip rule
                continue

            if response_rule.matches(message):
                RESPONSES_COUNT.labels(chat_id=chat.id, rule=response_rule.__id__).inc()
                return response_rule.get_response(chat, sender, normalized_message)

    @staticmethod
    def _normalize(message: str):
        """
        Normalize message for easier processing
        :param message: original message
        :return: normalized message
        """
        # remove duplicate whitespaces from the message
        normalized_message = re.sub(' +', ' ', message)
        # we will only parse the message in lower case
        normalized_message = normalized_message.lower()
        # remove all characters from the message except the given ones
        normalized_message = re.sub('[^a-z0-9| ?]+', '', normalized_message)
        return normalized_message
