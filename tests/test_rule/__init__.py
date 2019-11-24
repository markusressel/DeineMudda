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
from tests import TestBase


class RuleTest(TestBase):

    def test_genitive_first_rule(self):
        from deinemudda.response.rule.deinemudda import GenitiveFirstRule
        rule = GenitiveFirstRule()

        positive_samples = [
            "Wen?",
            "Wen soll ich fragen?",
            "Und wen genau frage ich da?",
        ]

        for match in positive_samples:
            self.assertTrue(rule.matches(match))

    def test_genitive_second_rule(self):
        from deinemudda.response.rule.deinemudda import GenitiveSecondRule
        rule = GenitiveSecondRule()

        positive_samples = [
            "Wessen?",
            "Wessen auto ist das?",
            "Und wessen genau?",
        ]

        for match in positive_samples:
            self.assertTrue(rule.matches(match))

    def test_dativ_rule(self):
        from deinemudda.response.rule.deinemudda import DativRule
        rule = DativRule()

        positive_samples = [
            "Wem?",
            "Wem gebe ich das?",
            "Und wem genau sage ich das?",
        ]

        for match in positive_samples:
            self.assertTrue(rule.matches(match))

    def test_who_german_rule(self):
        from deinemudda.response.rule.deinemudda import WhoGermanRule
        rule = WhoGermanRule()

        positive_samples = [
            "Wer?",
            "Wer ist das?",
            "Und wer genau?",
        ]

        for match in positive_samples:
            self.assertTrue(rule.matches(match))

    def test_why_german_rule(self):
        from deinemudda.response.rule.deinemudda import WhyRule
        rule = WhyRule()

        positive_samples = [
            "Wieso?",
            "Weshalb?",
            "Warum?",
            "Warum das denn?",
            "Und warum genau?",
        ]

        for match in positive_samples:
            self.assertTrue(rule.matches(match))
