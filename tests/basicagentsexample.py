from __future__ import annotations

import dataclasses
import math

import trio

from moves import autils


@dataclasses.dataclass
class Input:
    cmd: str


@dataclasses.dataclass
class Output:
    result: str


async def ins(in_send: trio.MemorySendChannel[Input]) -> None:
    'simple fast producer: creates 10 inputs and send them'

    async with in_send:
        for cmd in (f'cmd{i}' for i in range(10)):
            input_ = Input(cmd=cmd)
            print(f'ins [{input_=}]')
            await in_send.send(input_)


async def logic(queue: trio.MemoryReceiveChannel[Input],
                out_send: autils.MemorySendChannel[Output]) -> None:
    '''slow "brain"

    it is basically a state machine, that reads Inputs from queue, react
    transforming the Input cmd in an Output result, and send it to out_send

    force the slowness with a sleep (think some heavy calculations)
    '''

    async with queue, out_send:
        async for input_ in queue:
            print(f'logic [{input_=}]')
            cmd = input_.cmd
            await trio.sleep(3)
            result = f'result{cmd[3:]}'
            output = Output(result=result)
            print(f'logic [{output=}]')
            await out_send.send(output)


async def output(msg: str,
                 output_queue: trio.MemoryReceiveChannel[Output]
                 ) -> None:
    'simple consumer: just print out every Output it receive'

    async with output_queue:
        async for output in output_queue:
            print(f'output [{msg=}, {output=}]')


async def main() -> None:
    print(f'main()')
    async with trio.open_nursery() as nursery:
        in_send, in_receive = trio.open_memory_channel[Input](math.inf)
        out_send, (out_receive0, out_receive1,
                   out_receive2) = autils.open_memory_channel_tee[Output](3, math.inf)

        async with in_send, in_receive, \
                out_send, out_receive0, out_receive1, out_receive2:

            nursery.start_soon(ins, in_send.clone())
            nursery.start_soon(logic, in_receive.clone(), out_send.clone())
            nursery.start_soon(output, 'UNO', out_receive0.clone())
            nursery.start_soon(output, 'DUE', out_receive1.clone())
            nursery.start_soon(output, 'TRE', out_receive2.clone())


if __name__ == '__main__':
    trio.run(main)
