import logging
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
        input_send, input_receive = trio.open_memory_channel[types.InputQueueElement](0)
        output_send, output_receive1, output_receive2 = autils.open_memory_channel_tee(types.OutputQueueElement, 0)

        LOGS.info('parent')

        async with autils.ctxms(input_send, input_receive,
                                output_send, output_receive1, output_receive2):
            # game engine
            nursery.start_soon(game_engine.game_engine,
                               input_receive.clone(),
                               output_send.clone())

            # input from humans (+ create world)
            nursery.start_soon(rest.rest,
                               input_send.clone())
            # output to humans
            nursery.start_soon(amq_client.amq_client,
                               output_receive1.clone())

            # input and output from/to cpu
            nursery.start_soon(cpu.cpu,
                               input_send.clone(),
                               output_receive2.clone())


def main():
    trio.run(parent)
