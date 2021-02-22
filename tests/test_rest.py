from __future__ import annotations

from math import inf
from typing import List
from typing import Optional
from unittest import TestCase

from async_generator import aclosing
from chess import Board
from trio import BrokenResourceError
from trio import open_memory_channel
from trio import open_nursery

from moves.rest.constants import INPUT_TOPIC
from moves.rest.constants import OUTPUT_TOPIC
from moves.rest.cpu import cpu
from moves.rest.types import GameUniverse
from moves.rest.types import InputQueueElement
from moves.rest.types import OutputQueueElement
from moves.rest.types import Player
from moves.rest.types import PlayerType
from moves.rest.types import Result
from moves.triopubsub import Broker

from ._support_for_tests import atake
from ._support_for_tests import timeout
from ._support_for_tests import trio_test


async def run(n: int,
              outputs: List[Optional[OutputQueueElement]]) -> List[InputQueueElement]:
    b = Broker()
    b.add_topic(INPUT_TOPIC, InputQueueElement)
    b.add_topic(OUTPUT_TOPIC, OutputQueueElement)

    acc: List[InputQueueElement] = []
    async with open_nursery() as nursery:
        nursery.start_soon(cpu, b)

        async def producer() -> None:
            for output in outputs:
                b.send(output, OUTPUT_TOPIC)
        nursery.start_soon(producer)

        async def consumer() -> None:
            acc.extend(await atake(n, b.subscribe_topic(INPUT_TOPIC,
                                                        InputQueueElement)))
        nursery.start_soon(consumer)
    return acc


GAME_UNIVERSE = GameUniverse(game_id='game_id',
                             board=Board(),
                             white=Player('pid1', PlayerType.HUMAN, 'pname1'),
                             black=Player('pid2', PlayerType.HUMAN, 'pname2'))


class TestRest(TestCase):
    @trio_test
    @timeout(5)
    async def test_cpu(self) -> None:
        outputs = [OutputQueueElement(result=Result.GAME_CREATED,
                                      game_universe=GAME_UNIVERSE),
                   None]
        expected: List[InputQueueElement] = []
        actual: List[InputQueueElement] = await run(0, outputs)
        self.assertListEqual(expected, actual)

    @trio_test
    @timeout(5)
    async def test_take_from_infinite_loop(self) -> None:
        acc: List[int] = []
        async with open_nursery() as nursery:
            s, r = open_memory_channel[int](inf)

            async def p()->None:
                try:
                    async with aclosing(s) as s2:
                        while True:
                            await s2.send(1)
                except BrokenResourceError:
                    pass
            nursery.start_soon(p)

            async def c() -> None:
                async with aclosing(r) as r2:
                    acc.extend(await atake(3, r2))
            nursery.start_soon(c)

        print(acc)
