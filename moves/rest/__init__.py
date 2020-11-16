import trio

from .amq_client import amq_client
from .game_engine import game_engine
from .rest import rest


async def parent() -> None:
    async with trio.open_nursery() as nursery:
        (input_send, input_receive) = trio.open_memory_channel(0)
        (output_send, output_receive) = trio.open_memory_channel(0)

        async with input_send, input_receive, output_send, output_receive:
            nursery.start_soon(rest,
                               input_send.clone(),
                               output_receive.clone())
            nursery.start_soon(game_engine,
                               input_receive.clone(),
                               output_send.clone())
            nursery.start_soon(amq_client,
                               output_receive.clone())


def main():
    trio.run(parent)
