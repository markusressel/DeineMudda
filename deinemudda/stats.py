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

MESSAGE_TIME = Summary('message_processing_seconds', 'Time spent in the messages handler')


def get_metrics() -> []:
    entries = set()
    for name, obj in globals().items():
        if isinstance(obj, MetricWrapperBase):
            entries.add(obj)

    return list(entries)
