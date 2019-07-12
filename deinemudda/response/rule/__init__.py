from deinemudda.persistence import Persistence


class ResponseRule:

    def __init__(self, persistence: Persistence):
        self._persistence = persistence

    @property
    def description(self):
        """
        :return: A description of what this rule is about
        """
        raise NotImplementedError()

    def matches(self, message: str):
        raise NotImplementedError()

    def get_response(self, sender: str, message: str):
        raise NotImplementedError()
