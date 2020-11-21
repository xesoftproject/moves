from __future__ import annotations

import dataclasses
import math
import unittest

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


async def deals(in_receive: trio.MemoryReceiveChannel[Input],
                out_send: autils.MemorySendChannel[Output]) -> None:
    '''slow "brain"

    it is basically a state machine, that reads Inputs from in_receive, react
    transforming the Input cmd in an Output result, and send it to out_send

    force the slowness with a sleep (think some heavy calculations)
    '''

    async with in_receive, out_send:
        async for input_ in in_receive:
            print(f'deals [{input_=}]')
            cmd = input_.cmd
            await trio.sleep(3)
            result = f'result{cmd[3:]}'
            output = Output(result=result)
            print(f'deals [{output=}]')
            await out_send.send(output)


async def outs(msg: str,
               out_receive: trio.MemoryReceiveChannel[Output]
               ) -> None:
    'simple consumer: just print out every Output it receive'

    async with out_receive:
        async for output in out_receive:
            print(f'outs [{msg=}, {output=}]')


async def main() -> None:
    print(f'main()')
    async with trio.open_nursery() as nursery:
        in_send, in_receive = trio.open_memory_channel[Input](math.inf)  # <---
        out_send, out_receives = autils.open_memory_channel_tee(Output, 3, 0)

        async with autils.ctxms(in_send, in_receive, out_send, *out_receives):
            itor = iter(out_receives)

            nursery.start_soon(ins, in_send.clone())
            nursery.start_soon(deals, in_receive.clone(), out_send.clone())
            nursery.start_soon(outs, 'UNO', next(itor).clone())
            nursery.start_soon(outs, 'DUE', next(itor).clone())
            nursery.start_soon(outs, 'TRE', next(itor).clone())


class BasicAgentsExample(unittest.TestCase):
    def test_basic_agents_example(self):
        trio.run(main)


if __name__ == '__main__':
    unittest.main()