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
        input_send, input_receive = trio.open_memory_channel[types.InputQueueElement](
            math.inf)
        # from game_engine to external world (rest - for game id, cpu and amq)
        output_send, output_receives = autils.open_memory_channel_tee(
            types.OutputQueueElement, 3, 0)

        LOGS.info('parent')

        async with autils.ctxms(input_send, input_receive,
                                output_send, *output_receives):
            # game engine
            nursery.start_soon(game_engine.game_engine,
                               input_receive.clone(),
                               output_send.clone())

            # input from humans (+ create world)
            nursery.start_soon(rest.rest,
                               input_send.clone(),
                               output_receives[0].clone())
            # output to humans
            nursery.start_soon(amq_client.amq_client,
                               output_receives[1].clone())

            # input and output from/to cpu
            nursery.start_soon(cpu.cpu,
                               input_send.clone(),
                               output_receives[2].clone())


def main():
    trio.run(parent)
