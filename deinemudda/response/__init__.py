import re
from random import random

from deinemudda import util
from deinemudda.persistence import Persistence, Chat
from deinemudda.response.rule import ResponseRule


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

    def process_message(self, chat: Chat, sender: str, message: str) -> str or None:
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

        for rule in self.response_rules:
            # TODO: get trigger chance for specific rule based on chat id
            # trigger_chance = int(chat.get_setting("{}-TriggerChance".format(rule.__id__), default="1"))
            trigger_chance = int(chat.get_setting("TriggerChance", default="1"))

            if random() >= trigger_chance:
                # skip rule
                continue

            if rule.matches(message):
                return rule.get_response(chat, sender, normalized_message)

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
