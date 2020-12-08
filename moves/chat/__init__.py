from __future__ import annotations

import dataclasses
import json
import logging
import typing

import hypercorn.config
import hypercorn.trio
import quart
import quart_trio
import trio
import quart_cors

from .. import configurations
from .. import logs


LOGS = logging.getLogger(__name__)


@dataclasses.dataclass
class Message:
    from_: str
    body: str

    @classmethod
    def loads(cls, data: str):
        return cls(**json.loads(data))

    def dumps(self) -> str:
        return json.dumps(dataclasses.asdict(self))


@dataclasses.dataclass
class Chat:
    messages: typing.List[Message] = dataclasses.field(default_factory=list)
    websockets: typing.Set[typing.Any] = dataclasses.field(default_factory=set)
    channel = trio.open_memory_channel[Message](0)


CHATS: typing.Dict[str, Chat] = {}
CHATS['12345'] = Chat()


async def broadcast_per_game_id(c):
    async for message in c.channel[1]:
        for websocket in c.websockets:
            await websocket.send(message.dumps())


async def broadcast():
    async with trio.open_nursery() as nursery:
        while True:
            await trio.sleep(0)
            for c in CHATS.values():
                nursery.start_soon(broadcast_per_game_id, c)


async def chat() -> None:
    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.CHAT_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    app = typing.cast(quart_trio.QuartTrio,
                      quart_cors.cors(quart_trio.QuartTrio(__name__),
                                      allow_origin='*',
                                      allow_methods=['POST'],
                                      allow_headers=['content-type']))

    @app.websocket('/chats')
    async def chats() -> None:
        for chat_id in CHATS.keys():
            await quart.websocket.send(chat_id)

    @app.route('/chat/<string:chat_id>', methods=['POST'])
    async def create_chat(chat_id: str) -> str:
        CHATS[chat_id] = Chat()
        return chat_id

    @app.websocket('/chat/<string:chat_id>')
    async def chat(chat_id: str) -> None:
        c = CHATS[chat_id]
        c.websockets.add(quart.websocket._get_current_object())

        # send old messages
        for message in c.messages:
            await quart.websocket.send(message.dumps())

        while True:
            # new message
            message = Message.loads(await quart.websocket.receive())

            c.messages.append(message)

            # notifica broadcast
            await c.channel[0].send(message)

    async with trio.open_nursery() as nursery:
        nursery.start_soon(hypercorn.trio.serve, app, config)
        nursery.start_soon(broadcast)


def main() -> None:
    logs.setup_logs(__name__)

    trio.run(chat)
