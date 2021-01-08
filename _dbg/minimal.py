import asyncio

import trio
import trio_asyncio


async def main() -> None:
    async with trio_asyncio.open_loop() as loop:
        await trio_asyncio.aio_as_trio(loop.subprocess_exec)(asyncio.SubprocessProtocol,
                                                             '/bin/sleep', '5')
trio.run(main)
