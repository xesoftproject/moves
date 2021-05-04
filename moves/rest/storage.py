# load and save messages from file

from io import StringIO
from typing import Any
from typing import DefaultDict
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union
from typing import overload

from jsonlines import Reader
from jsonlines import Writer
from jsonlines import open

from ..triopubsub import Broker
from ..triopubsub import Topic

T = TypeVar('T')

# storage format: a journal, append-only "jsonl" format
DEFAULT_FN = 'storage.jsonl'


@overload
def load_broker(fn_io: str = DEFAULT_FN) -> Broker: ...


@overload
def load_broker(
    fn_io: StringIO,
    broker: Optional[Broker] = None) -> Broker: ...


def load_broker(fn_io: Union[str, StringIO] = DEFAULT_FN,
                broker: Optional[Broker] = None) -> Broker:
    old_messages = DefaultDict[str, List[Any]](list)
    try:
        with (open(fn_io, 'r')
              if isinstance(fn_io, str)
              else Reader(fn_io)) as reader:
            for message, topic_id in reader:
                old_messages[topic_id].append(message)
    except OSError:
        pass

    def on_add_topic(topic_id: str, topic: Topic[T]) -> None:
        'pre-fill topic with old messages'
        for old_message in old_messages[topic_id]:
            topic.send(old_message)

    def on_send(message: Any, topic_id: str) -> None:
        'keep track of the message sent'
        with (open(fn_io, 'a')
              if isinstance(fn_io, str)
              else Writer(fn_io)) as writer:
            writer.write((message, topic_id))

    b = broker if broker is not None else Broker()
    b.register_on_add_topic(on_add_topic)
    b.register_on_send(on_send)
    return b
