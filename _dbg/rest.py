import trio

from moves import logs
from moves import rest
from moves import web


async def main() -> None:
    async with trio.open_nursery() as nursery:
        nursery.start_soon(rest.parent)
        nursery.start_soon(web.web)

logs.setup_logs('')
trio.run(main)
