import chess.engine
import trio_asyncio

import moves.configurations.local


async def main() -> None:
    transport, engine = await trio_asyncio.aio_as_trio(chess.engine.popen_uci)('/mnt/c/' + moves.configurations.local.STOCKFISH)

    result = await trio_asyncio.aio_as_trio(engine.play)(chess.Board(), chess.engine.Limit(time=0.1))
    print(result)

    await trio_asyncio.aio_as_trio(engine.quit)()

trio_asyncio.run(main)
