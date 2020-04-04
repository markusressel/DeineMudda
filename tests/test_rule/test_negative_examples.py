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
from typing import List

from deinemudda.response import ResponseManager, ResponseRule
from tests import TestBase


class NegativeExamplesTest(TestBase):
    real_examples = [
        "vermutlich alles sars impfstoff abwandlungen",  # -> fail
        "der selbe",  # -> fail
        "Zander du Eumel, alles gute",  # -> fail
        "da flieg ich lieber nach bangladesch",  # -> fail
        "Könnte man dich eigentlich auch mal fragen",  # -> fail
        "manche leute müssen ja arbeiten weil sie auf nen thesis jam gezwungen wirden",  # -> fail
        "Jeden Tag was neues gelernt xD",  # -> fail
        "Roji - Taste of Japan Pankow",  # -> fail
        "Tut mir leid",  # -> fail
        "danke. mache mich gleich auf den Weg",  # -> fail
        "wenn du was raussuchst, auch gerne da",  # -> fail
    ]

    rules: List[ResponseRule] = ResponseManager._find_rules()

    def test_negative_examples(self):
        for rule in self.rules:
            for phrase in self.real_examples:
                self.assertFalse(rule.matches(phrase), f"Rule {rule.__id__} unexpectedly matched: {phrase}")
