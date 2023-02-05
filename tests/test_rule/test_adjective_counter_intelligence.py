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

from deinemudda.response.rule.deinemudda import AdjectiveCounterIntelligenceRule
from tests import TestBase


class AdjectiveCounterIntelligenceRuleTest(TestBase):

    def test_samples(self):
        rule = AdjectiveCounterIntelligenceRule()

        mapping = {
            "das ist doch gut geworden": ["doch", "gut"],
            "das ist doch sehr gut": ["doch", "sehr", "gut"],
            "der bot ist schlau": ["schlau"],
            # "markus ist eine kacknase": ["eine", "kacknase"],
            # "Satisfactory ist saugeil": ["saugeil"],
            "lol": [],
        }

        for input, expected_output in mapping.items():
            output = rule._find_adpj(input)
            self.assertEqual(expected_output, output)

    def test_multiple_words_1(self):
        rule = AdjectiveCounterIntelligenceRule()

        response = rule.get_response(self.dummy_chat, None, "das ist doch gut geworden")
        self.assertIn(response, [
            "deine mudda is' doch gut",
            "markus's mudda is' doch gut",
            "wie deine mudda beim kacken",
        ])

    def test_multiple_words(self):
        rule = AdjectiveCounterIntelligenceRule()

        response = rule.get_response(self.dummy_chat, None, "Ihr seid hässlich, dumm und doof")
        self.assertIn(response, [
            "deine mudda is' hässlich , dumm und doof",
            "markus's mudda is' hässlich , dumm und doof",
            "wie deine mudda beim kacken",
        ])
