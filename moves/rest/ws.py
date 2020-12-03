from __future__ import annotations

import collections
import logging
import math
import typing

import hypercorn.config
import hypercorn.trio
import quart
from quart.globals import websocket
import quart_trio
import trio

from . import types
from .. import configurations


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

        db: typing.DefaultDict[str, typing.Tuple[typing.List[str],
                                                 typing.Set[typing.Any]]] = collections.defaultdict(lambda: ([], set()))

        s,r = trio.open_memory_channel[typing.Tuple[str, str]](math.inf)

        async def broadcast():
            async for _, message in r:
                # TODO add per game_id
                for websocket in (ws for _,wss in db.values() for ws in wss):
                    await websocket.send(message)

        @app.websocket('/register/<string:game_id>')
        async def register(game_id: str) -> None:
            print(f'register({game_id=})')


            db[game_id][1].add(quart.websocket._get_current_object())

            # manda mosse vecchie
            for old_move in db[game_id][0]:
                print(f'register [{old_move=}]')
                await quart.websocket.send(old_move)

            while True:
                # arriva mossa nuova
                new_move = await quart.websocket.receive()
                print(f'register [{new_move=}]')

                # salvala
                db[game_id][0].append(new_move)

                # notifica broadcast
                await s.send((game_id, new_move))

        async with trio.open_nursery() as nursery:
            nursery.start_soon(hypercorn.trio.serve, app, config)
            nursery.start_soon(broadcast)
