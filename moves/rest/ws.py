from __future__ import annotations

import logging
import typing

import hypercorn.config
import hypercorn.trio
import quart
import quart_trio
import trio

from . import types
from .. import configurations
import collections
import math


LOGS = logging.getLogger(__name__)


Move = str


class S:
    def __init__(self):
        self.moves: typing.Deque[Move] = collections.deque()
        self.mscs: typing.Set[trio.MemorySendChannel[Move]] = set()
        self.mrcs: typing.Set[trio.MemoryReceiveChannel[Move]] = set()

    def __repr__(self):
        return f'S({self.moves}, {self.mscs}, {self.mrcs})'


async def ws(receive_channel: trio.MemoryReceiveChannel[types.OutputQueueElement]
             ) -> None:
    async with receive_channel:
        LOGS.info('ws')

        config = hypercorn.config.Config()
        config.bind = [f'0.0.0.0:{configurations.WS_PORT}']
        if configurations.CERTFILE:
            config.certfile = configurations.CERTFILE
        if configurations.KEYFILE:
            config.keyfile = configurations.KEYFILE

        app = quart_trio.QuartTrio(__name__)

        db: typing.DefaultDict[str, S] = collections.defaultdict(S)

        @app.websocket('/register/<string:game_id>')
        async def register(game_id: str) -> None:
            print(f'register({game_id=})')

            msc, mrc = trio.open_memory_channel[Move](math.inf)
            s = db[game_id]
            s.mscs.add(msc)
            s.mrcs.add(mrc)

            print(f'register [{s=}]')

            for move in s.moves:
                print(f'register [{move=}]')
                await msc.send(move)

            while True:
                data = await quart.websocket.receive()
                print(f'register [{data=}]')

                for msc in db[game_id].mscs:
                    print(f'register [{msc=}]')
                    await msc.send(data)

                for mrc in db[game_id].mrcs:
                    print(f'register [{mrc=}]')
                    async for msg in mrc:
                        print(f'register [{msg=}]')
                        await quart.websocket.send(msg)

        await hypercorn.trio.serve(app, config)
