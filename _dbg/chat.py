import trio

from moves import chat
from moves import web


async def main() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(chat.chat)
        nursery.start_soon(web.web)
trio.run(main)
