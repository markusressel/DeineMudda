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
from types import SimpleNamespace

from deinemudda.response.rule.deinemudda import AdjectiveCounterIntelligenceRule
from tests import TestBase


class AdjectiveCounterIntelligenceRuleTest(TestBase):

    def test_multiple_words(self):
        rule = AdjectiveCounterIntelligenceRule()

        dummy_chat = SimpleNamespace(users=[SimpleNamespace(first_name="markus")])

        # TODO: this will randomly fail due to random selection of response in rule...
        response = rule.get_response(dummy_chat, None, "Ihr seid hässlich, dumm und doof")
        self.assertIn(response, [
            "deine mudda is' hässlich , dumm und doof",
            "markus's mudda is' hässlich , dumm und doof",
            "wie deine mudda beim kacken",
        ])
