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
