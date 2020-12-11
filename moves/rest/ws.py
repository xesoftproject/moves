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
    raise Exception("move it inside rest")
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
                    await websocket.send_channel(message)

        async def broadcast():
            async with trio.open_nursery() as nursery:
                while True:
                    await trio.sleep(0)
                    # per ogni partita
                    for s in db.values():
                        nursery.start_soon(broadcast_per_game_id, s)

        @app.websocket('/register/<string:game_id>')
        async def register(game_id: str) -> None:
            LOGS.info('register(%s)', game_id)

            db[game_id].websockets.add(quart.websocket._get_current_object())

            # manda mosse vecchie
            for old_move in db[game_id].moves:
                await quart.websocket.send_channel(old_move)

            # mantieni la connessione aperta (needed?)
            await trio.sleep_forever()

        async def consume_queue():
            async for output_element in receive_channel:
                LOGS.info('output_element: %s', output_element)

                body = json.dumps({
                    'move': output_element.move,
                    'table': str(output_element.game_universe.board)
                })
                game_id = output_element.game_universe.game_id

                db[game_id].moves.append(body)
                await db[game_id].channel[0].send_channel(body)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(hypercorn.trio.serve, app, config)
            nursery.start_soon(broadcast)
            nursery.start_soon(consume_queue)
