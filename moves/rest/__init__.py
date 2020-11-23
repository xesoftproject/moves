import logging
import math
import typing

import trio

from . import amq_client
from . import cpu
from . import game_engine
from . import rest
from . import types
from .. import autils


LOGS = logging.Logger(__name__)


async def parent() -> None:
    async with trio.open_nursery() as nursery:
        # from external world (just rest for now) to game_engine
        game_engine_send_channel, game_engine_receive_channel = trio.open_memory_channel[types.InputQueueElement](
            math.inf)
        # from game_engine to external world (rest - for game id, cpu and amq)
        multiple_send_channel, (rest_receive_channel, amq_client_receive_channel,
                                cpu_receive_channel) = autils.open_memory_channel_tee[types.OutputQueueElement](3, math.inf)

        LOGS.info('parent')

        async with game_engine_send_channel, game_engine_receive_channel, \
                multiple_send_channel, \
                rest_receive_channel, \
                amq_client_receive_channel, \
                cpu_receive_channel:
            # game engine
            nursery.start_soon(game_engine.game_engine,
                               game_engine_receive_channel.clone(),
                               multiple_send_channel.clone())

            # input from humans (+ create world)
            nursery.start_soon(rest.rest,
                               game_engine_send_channel.clone(),
                               rest_receive_channel.clone())
            # output to humans
            nursery.start_soon(amq_client.amq_client,
                               amq_client_receive_channel.clone())

            # input and output from/to cpu
            nursery.start_soon(cpu.cpu,
                               game_engine_send_channel.clone(),
                               cpu_receive_channel.clone())


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    trio.run(parent)
