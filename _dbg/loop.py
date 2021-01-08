import datetime

import chess.engine
import trio
import trio_asyncio

import moves.configurations.local


class Delta:
    def __init__(self) -> None:
        self.now = datetime.datetime.now()

    def delta(self) -> datetime.timedelta:
        now = datetime.datetime.now()
        delta = now - self.now
        self.now = now
        return delta


async def foo(delta: Delta) -> None:
    for i in range(30):
        await trio.sleep(1)
        print(f'foo [{i=}, {delta.delta().total_seconds()=}]')


async def bar(delta: Delta) -> None:
    _, engine = await trio_asyncio.aio_as_trio(chess.engine.popen_uci)('/mnt/c/' + moves.configurations.local.STOCKFISH)
    board = chess.Board()
    while not board.is_game_over():
        result = await trio_asyncio.aio_as_trio(engine.play)(board, chess.engine.Limit(time=5))
        print(f'bar [{result=}, {delta.delta().total_seconds()=}]')
        if not result.move:
            raise Exception('no move!')
        board.push(result.move)

    await trio_asyncio.aio_as_trio(engine.quit)()


async def main() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(foo, Delta())

        async def wrapper(delta: Delta) -> None:
            async with trio_asyncio.open_loop():
                await bar(delta)

        nursery.start_soon(wrapper, Delta())


trio.run(main)
