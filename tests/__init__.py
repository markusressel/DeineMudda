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

import unittest
from types import SimpleNamespace
from typing import List

from deinemudda.response import ResponseRule, ResponseManager


class TestBase(unittest.TestCase):
    all_rules: List[ResponseRule] = ResponseManager._find_rules()
    dummy_chat = SimpleNamespace(users=[SimpleNamespace(first_name="markus")])

    def setUp(self):
        pass

    def tearDown(self):
        pass

    if __name__ == '__main__':
        unittest.main()
