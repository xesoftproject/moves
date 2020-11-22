from __future__ import annotations

import contextlib
import dataclasses
import math
import typing

import hypercorn.config
import hypercorn.trio
import quart_trio
import trio


@dataclasses.dataclass
class Input:
    payload: int


@dataclasses.dataclass
class Output:
    payload: int


async def logic(queue: trio.MemoryReceiveChannel[Input],
                send_tos: typing.List[trio.MemorySendChannel[Output]]
                ) -> None:
    'reads Inputs from queue, transform to Output and send it to send_tos'

    async with contextlib.AsyncExitStack() as stack:
        queue = await stack.enter_async_context(queue)
        send_tos = [await stack.enter_async_context(send_to)
                    for send_to in send_tos]

        async for input_ in queue:
            print(f'logic [{input_=}]')
            await trio.sleep(3)
            output = Output(input_.payload)
            print(f'logic [{output=}]')
            for send_to in send_tos:
                await send_to.send(output)


async def rest(send_channel: trio.MemorySendChannel[Input],
               receive_channel: trio.MemoryReceiveChannel[Output]) -> None:
    'the producer is the human calling the rest endpoints'

    async with send_channel, receive_channel:
        config = hypercorn.config.Config()
        config.bind = ['0.0.0.0:8080']

        app = quart_trio.QuartTrio(__name__)

        @app.route('/<int:payload>')
        async def hello(payload: int) -> str:
            input_ = Input(payload)
            print(f'rest [{input_=}]')

            await send_channel.send(input_)
            async for output in receive_channel:
                break

            print(f'ui [{output=}]')
            return str(output)

        await hypercorn.trio.serve(app, config)


async def output(output_queue: trio.MemoryReceiveChannel[Output]) -> None:
    'simple consumer: just print out every Output it receive'

    async with output_queue:
        async for output in output_queue:
            print(f'output [{output=}]')


async def ia(send_channel: trio.MemorySendChannel[Input],
             receive_channel: trio.MemoryReceiveChannel[Output]
             ) -> None:
    'consume from and then send ia to logic'

    async with send_channel, receive_channel:
        async for output in receive_channel:
            print(f'ia [{output=}]')
            if output.payload is None:
                break
            if output.payload > 0:
                input_ = Input(output.payload - 1)
                print(f'ia [{input_=}]')
                await send_channel.send(input_)


async def main() -> None:
    async with trio.open_nursery() as nursery:
        logic_send_channel, logic_receive_channel = trio.open_memory_channel[Input](
            math.inf)
        ui_send_channel, ui_receive_channel = trio.open_memory_channel[Output](
            math.inf)
        output_send_channel, output_receive_channel = trio.open_memory_channel[Output](
            math.inf)
        ia_send_channel, ia_receive_channel = trio.open_memory_channel[Output](
            math.inf)

        async with logic_send_channel, logic_receive_channel, \
                ui_send_channel, ui_receive_channel, \
                output_send_channel, output_receive_channel:

            nursery.start_soon(logic, logic_receive_channel.clone(),
                               [ui_send_channel.clone(),
                                output_send_channel.clone(),
                                ia_send_channel.clone()])

            nursery.start_soon(rest, logic_send_channel.clone(),
                               ui_receive_channel.clone())
            nursery.start_soon(output, output_receive_channel.clone())
            nursery.start_soon(ia, logic_send_channel.clone(),
                               ia_receive_channel.clone())


if __name__ == '__main__':
    trio.run(main)
