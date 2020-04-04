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

from abc import abstractmethod

from deinemudda.persistence import Chat


class ResponseRule:

    @property
    def __id__(self) -> str:
        """
        :return: a unique identifier for this rule
        """
        return self.__class__.__name__

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
    def matches(self, message: str) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def get_response(self, chat: Chat, sender: str, message: str) -> str or None:
        raise NotImplementedError()
