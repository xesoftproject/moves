# load and save messages from file

from functools import wraps
from typing import Any
from typing import Callable
from typing import Literal
from typing import Tuple
from typing import TypeVar
from typing import Union

from jsonlines import open

from ..triopubsub import Broker

T = TypeVar('T')

# storage format: a journal, append-only "jsonl" format
DEFAULT_FN = 'storage.jsonl'


Operation = Union[Tuple[Literal['add_topic'], str],
                  Tuple[Literal['send'], Any, str]]


def load_broker(broker: Broker, fn: str=DEFAULT_FN) -> None:
    # supported operation: add_topic, send

    try:
        ops = open(fn, 'r')
    except FileNotFoundError:
        return
    else:
        with ops as operations:
            for operation in operations:
                if operation[0] == 'add_topic':
                    topic_id = operation[1]
                    broker.add_topic(topic_id, type)  # Type[Any] is not a type
                elif operation[0] == 'send':
                    message, topic_id = operation[1:]
                    broker.send(message, topic_id)


async def update_broker(broker: Broker, fn: str=DEFAULT_FN) -> None:
    def add_signal(method: Callable[..., Any],
                   signal: Callable[..., None]) -> Callable[..., Any]:
        @wraps(method)
        def wrapper(*args: Any) -> Any:
            signal(*args)
            return method(*args)
        return wrapper

    def append(operation: Operation) -> None:
        with open(fn, 'a') as writer:
            writer.write(operation)

    broker.add_topic = add_signal(broker.add_topic,  # type: ignore
                                  lambda topic_id, _: append(('add_topic', topic_id)))
    broker.send = add_signal(broker.send,  # type: ignore
                             lambda message, topic_id: append(('send', message, topic_id)))
