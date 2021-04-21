from logging import Logger

from trio import open_nursery
from trio import run

from ..configurations import running_on_ec2
from ..logs import setup_logs
from ..triopubsub import Broker
from .constants import INPUT_TOPIC
from .constants import OUTPUT_TOPIC
from .cpu import cpu
from .game_engine import game_engine
from .rest import rest
from .types import InputQueueElement
from .types import OutputQueueElement

setup_logs(__name__)
LOGS = Logger(__name__)


async def parent() -> None:
    '''Main entry point; the goal is to juggle 3 actors:
    - game_engine: the games (plural)
    - cpu: pc players (plural)
    - rest: human players (plural)

    game_engine handle incoming messages to create a game, apply a move, etc...
                send messages to players (pc and human) to propagate the moves
    cpu handle incoming messages to deal with a move
        send messages to game_engine to signal a move
    rest is similar to cpu, but exposes the API trough REST/WS endpoints
    '''

    # 2 topics (in+out) - the needed subscription will be created by each task
    broker = Broker()
    broker.add_topic(INPUT_TOPIC, InputQueueElement)
    broker.add_topic(OUTPUT_TOPIC, OutputQueueElement)

    try:
        async with open_nursery() as nursery:
            # game engine
            nursery.start_soon(game_engine, broker)

            # input and output from/to humans
            nursery.start_soon(rest, broker)

            # input and output from/to cpu
            nursery.start_soon(cpu, broker)
    finally:
        await broker.remove_topic(INPUT_TOPIC)
        await broker.remove_topic(OUTPUT_TOPIC)
        await broker.aclose()


def main() -> None:
    if running_on_ec2():
        from trio_asyncio import run as trio_asyncio_run
        trio_asyncio_run(parent)
    else:
        run(parent)
