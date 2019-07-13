from abc import abstractmethod

from deinemudda.persistence import Persistence


class ResponseRule:

    def __init__(self, persistence: Persistence):
        self._persistence = persistence

    @property
    @abstractmethod
    def __id__(self) -> str:
        """
        :return: a unique identifier for this rule
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def __description__(self) -> str:
        """
        :return: A description of what this rule is about
        """
        raise NotImplementedError()

    @property
    def __priority__(self) -> float:
        return 0.0

    @abstractmethod
    def matches(self, message: str):
        raise NotImplementedError()

    @abstractmethod
    def get_response(self, sender: str, message: str):
        raise NotImplementedError()
