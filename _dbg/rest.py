import trio

from moves import rest
from moves import web


async def main():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(rest.parent)
        nursery.start_soon(web.web)

trio.run(main)
