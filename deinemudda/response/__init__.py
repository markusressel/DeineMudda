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
from typing import List, Tuple

from deinemudda import util
from deinemudda.const import SETTINGS_TRIGGER_PROBABILITY_KEY, SETTINGS_TRIGGER_PROBABILITY_DEFAULT, \
    VOTE_BUTTON_ID_THUMBS_UP, VOTE_BUTTON_ID_THUMBS_DOWN
from deinemudda.persistence import Persistence, Chat
from deinemudda.persistence.entity.chat import VoteMenu
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

    @staticmethod
    def _find_rules() -> List[ResponseRule]:
        """
        :return: list of rules
        """
        from deinemudda.response import rule
        rule_classes = util.find_implementations(ResponseRule, rule)
        # construct implementations
        rule_instances = list(map(lambda x: x(), rule_classes))
        return sorted(rule_instances, key=lambda x: x.__priority__, reverse=True)

    def find_matching_rule(self, chat: Chat, sender: str, message: str) -> Tuple[ResponseRule or None, str or None]:
        """
        Processes the given message and returns a response if one of the response rules match
        :param chat: the chat this message was sent in
        :param sender: the message sender
        :param message: the message
        :return: (Rule, Response message) tuple which may contain None
        """
        normalized_message = self._normalize(message)

        # print tags and chunks for debugging
        # TODO: use logger for this and don't log in production at all
        # pprint()
        # from pattern import text
        # parsed = text.parse(normalized_message, relations=True, lemmata=True)

        global_trigger_chance = float(chat.get_setting(SETTINGS_TRIGGER_PROBABILITY_KEY,
                                                       default=SETTINGS_TRIGGER_PROBABILITY_DEFAULT))
        if random() >= global_trigger_chance:
            # do not respond
            return None, None

        for response_rule in self.response_rules:
            # TODO: get trigger chance for specific rule based on chat id
            # trigger_chance = int(chat.get_setting("{}-TriggerChance".format(response_rule.__id__), default="1"))

            if response_rule.matches(message):
                response = response_rule.get_response(chat, sender, normalized_message)

                if not response:
                    continue

                if self._response_is_bad(response_rule, response):
                    # omit this response since we know users won't like it
                    continue

                RESPONSES_COUNT.labels(chat_id=chat.id, rule=response_rule.__id__).inc()
                return response_rule, response

        return None, None

    def _response_is_bad(self, rule: ResponseRule, response: str) -> bool:
        rating = self._persistence.get_response_rating(rule.__id__, response)
        return rating < 0

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
        normalized_message = re.sub('[^a-z0-9äöüß| ?]+', '', normalized_message)
        return normalized_message

    def evaluate(self, vote_menu: VoteMenu):
        """
        Evaluates a vote menu to learn from it
        :param vote_menu: the vote menu
        """
        with self._persistence._session_scope() as session:
            vote_menus = self._persistence.find_vote_menus_by_rule(session, vote_menu.rule_id, vote_menu.rule_trigger)

            positive_votes_total = 0
            negative_votes_total = 0
            for vote_menu in vote_menus:
                chat = vote_menu.chat
                chat_user_count = len(chat.users)

                positive_votes = vote_menu.item_count(VOTE_BUTTON_ID_THUMBS_UP)
                negative_votes = vote_menu.item_count(VOTE_BUTTON_ID_THUMBS_DOWN)
                total_votes = positive_votes + negative_votes
                if total_votes < (chat_user_count / 3):
                    LOGGER.debug(
                        f"Not enough votes ({total_votes}/{chat_user_count}) for meaningful result from vote menu {vote_menu.id} in chat {chat.id}")
                    continue

                positive_votes_total += positive_votes
                negative_votes_total += negative_votes

            voting_result = positive_votes_total - negative_votes_total
            messages = list(map(lambda x: x.message_text, vote_menus))
            LOGGER.debug(
                f"New response rating {voting_result} (+{positive_votes_total} vs -{negative_votes_total})"
                f" for messages: {messages}")
            for message in messages:
                self._persistence.add_or_update_response_rating(vote_menu.rule_id, message, voting_result)
