import re

from deinemudda import util
from deinemudda.persistence import Persistence
from deinemudda.response.rule import ResponseRule


class ResponseManager:

    def __init__(self, persistence: Persistence):
        self._persistence = persistence
        self.response_rules = self._find_rules()

    def _find_rules(self):
        """
        :return: list of rules
        """
        from deinemudda.response import rule
        rule_classes = util.find_implementations(ResponseRule, rule)
        # construct implementations
        rule_instances = list(map(lambda x: x(self._persistence), rule_classes))
        return sorted(rule_instances, key=lambda x: x.priority, reverse=True)

    def process_message(self, sender: str, message: str) -> str or None:
        """
        Processes the given message and returns a response if one of the response rules match
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
            # TODO: get trigger change for specific rule based on chat id
            if rule.matches(message):
                return rule.get_response(sender, normalized_message)

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
