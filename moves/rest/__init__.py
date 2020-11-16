import typing

import trio

from . import types
from .amq_client import amq_client
from .cpu import cpu
from .game_engine import game_engine
from .rest import rest

import logging

LOGS = logging.Logger(__name__)


async def parent() -> None:
    async with trio.open_nursery() as nursery:
        input_send, input_receive = trio.open_memory_channel[types.InputQueueElement](0)
        output_send, output_receive = trio.open_memory_channel[types.OutputQueueElement](0)

        LOGS.info('parent')

        async with input_send, input_receive, output_send, output_receive:
            # game engine
            nursery.start_soon(game_engine,
                               input_receive.clone(),
                               output_send.clone())

            # input from humans (+ create world)
            nursery.start_soon(rest,
                               input_send.clone())
            # output to humans
            nursery.start_soon(amq_client,
                               output_receive.clone())

            # input and output from/to cpu
            nursery.start_soon(cpu,
                               input_send.clone(),
                               output_receive.clone())

def main():
    trio.run(parent)
