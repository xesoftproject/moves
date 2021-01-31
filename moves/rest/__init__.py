import logging
import math
import typing

import trio

from . import constants
from . import cpu
from . import game_engine
from . import rest
from . import types
from .. import autils
from .. import configurations
from .. import logs
from .. import triopubsub


LOGS = logging.Logger(__name__)


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
    broker = triopubsub.Broker()
    await broker.add_topic(constants.INPUT_TOPIC, types.InputQueueElement)
    await broker.add_topic(constants.OUTPUT_TOPIC, types.OutputQueueElement)

    async with trio.open_nursery() as nursery:
        # game engine
        nursery.start_soon(game_engine.game_engine, broker)

        # input and output from/to humans
        nursery.start_soon(rest.rest, broker)

        # input and output from/to cpu
        nursery.start_soon(cpu.cpu, broker)


def main() -> None:
    logs.setup_logs(__name__)

    if configurations.running_on_ec2():
        import trio_asyncio
        trio_asyncio.run(parent)
    else:
        trio.run(parent)
