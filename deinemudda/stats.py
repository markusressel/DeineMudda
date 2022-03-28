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

from prometheus_client import Gauge, Summary
from prometheus_client.metrics import MetricWrapperBase

MESSAGES_COUNT = Gauge('messages_count',
                       'Number of messages received and analysed',
                       ['chat_id'])
RESPONSES_COUNT = Gauge('responses_count',
                        'Number of responses sent back to the chat',
                        ['chat_id', 'rule'])

ENTITIES_COUNT = Gauge('entities_count',
                       'Number of entities with the given type',
                       ['type'])

USERS_IN_CHAT_COUNT = Gauge('users_in_chat',
                            'Number of user entities within the given chat',
                            ['chat_id'])

MESSAGE_TIME = Summary('message_processing_seconds', 'Time spent in the messages handler')


def get_metrics() -> []:
    entries = set()
    for name, obj in globals().items():
        if isinstance(obj, MetricWrapperBase):
            entries.add(obj)

    return list(entries)


def format_metrics() -> str:
    def format_sample(sample):
        result = "  "
        if len(sample[0]) > 0:
            result += str(sample[0])
        if len(sample[1]) > 0:
            result += str(sample[1])

        if len(result) > 0:
            result += " "
        result += str(sample[2])

        return result

    def format_samples(samples):
        return "\n".join(list(map(format_sample, samples)))

    def format_metric(metric):
        name = metric._name
        samples = list(metric._samples())
        samples_text = format_samples(samples)

        return f"{name}:\n{samples_text}"

    return "\n\n".join(map(format_metric, get_metrics()))
