from __future__ import annotations

import collections
import json
import logging
import typing

import hypercorn.config
import hypercorn.trio
import quart
import quart_trio
import trio

from . import types
from .. import configurations


LOGS = logging.getLogger(__name__)


class S:
    'Oggetto che rappresenta i dati di connessione per game_id'

    def __init__(self):
        # lista di mosse ['a1a2','b1b3',...]
        self.moves: typing.List[str] = []
        # insieme di client connessi set(ws-client-1, ws-client-2, ...)
        self.websockets: typing.Set[typing.Any] = set()
        # coda per i messaggi che andranno su tutte le websockets
        self.channel: typing.Tuple[trio.MemorySendChannel[str],
                                   trio.MemoryReceiveChannel[str]] = trio.open_memory_channel[str](0)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.moves}, {self.websockets}, {self.channel})'


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

        async def broadcast_per_game_id(s):
            # per ogni messaggio da inviare
            async for message in s.channel[1]:
                # per ogni client connesso
                for websocket in s.websockets:
                    # manda il messaggio a quel client
                    await websocket.send(message)

        async def broadcast():
            async with trio.open_nursery() as nursery:
                while True:
                    await trio.sleep(0)
                    # per ogni partita
                    for s in db.values():
                        nursery.start_soon(broadcast_per_game_id, s)
            print("ended")

        @app.websocket('/register/<string:game_id>')
        async def register(game_id: str) -> None:
            print(f'register({game_id=})')

            db[game_id].websockets.add(quart.websocket._get_current_object())

            # manda mosse vecchie
            for old_move in db[game_id].moves:
                print(f'register [{old_move=}]')
                await quart.websocket.send(json.dumps((game_id, old_move)))

            while True:
                # arriva mossa nuova
                new_move = await quart.websocket.receive()
                print(f'register [{new_move=}]')

                # salvala
                db[game_id].moves.append(new_move)

                # notifica broadcast
                await db[game_id].channel[0].send(json.dumps((game_id, new_move)))

        async with trio.open_nursery() as nursery:
            nursery.start_soon(hypercorn.trio.serve, app, config)
            nursery.start_soon(broadcast)
