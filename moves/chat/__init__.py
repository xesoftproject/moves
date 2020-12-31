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
from .. import autils
from .. import triopubsub


LOGS = logging.getLogger(__name__)


@dataclasses.dataclass
class ChatMessage:
    from_: str
    body: str

    @classmethod
    def loads(cls: 'typing.Type[ChatMessage]', data: str) -> 'ChatMessage':
        return cls(**json.loads(data))

    def dumps(self) -> str:
        return json.dumps(dataclasses.asdict(self))


async def chat() -> None:
    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.CHAT_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    # each "chat room" is a topic. for each connection there is a subscription
    broker = triopubsub.Broker()
    # + there is a "chats" topic - with just the list of the topic_ids
    chats_topic = broker.add_topic(triopubsub.Topic[str]('__chats'))

    app = typing.cast(quart_trio.QuartTrio,
                      quart_cors.cors(quart_trio.QuartTrio(__name__),
                                      allow_origin='*',
                                      allow_methods=['POST'],
                                      allow_headers=['content-type']))

    @app.websocket('/chats')
    async def chats() -> None:
        'sync the currently open chats'

        await quart.websocket.accept()

        async with broker.with_tmp_subscription(chats_topic.topic_id,
                                                str) as subscription:
            async for message in broker.messages(subscription.subscription_id,
                                                 str):
                await quart.websocket.send(message)

    @app.route('/chat/<string:chat_id>', methods=['POST'])
    async def create_chat(chat_id: str) -> str:
        'create a new chat'

        broker.add_topic(triopubsub.Topic[ChatMessage](chat_id))

        await broker.send_message_to(chat_id, chats_topic.topic_id)

        return chat_id

    @app.websocket('/chat/<string:chat_id>')
    async def chat(chat_id: str) -> None:
        'join a chat'

        async def send_messages() -> None:
            while True:
                chat_message = ChatMessage.loads(await quart.websocket.receive())
                await broker.send_message_to(chat_message, chat_id)

        async def receive_messages() -> None:
            async for message in broker.messages(subscription.subscription_id,
                                                 ChatMessage):
                await quart.websocket.send(message.dumps())

        async with broker.with_tmp_subscription(chat_id,
                                                ChatMessage) as subscription:
            async with trio.open_nursery() as nursery:
                nursery.start_soon(send_messages)
                nursery.start_soon(receive_messages)

    await hypercorn.trio.serve(app, config)


def main() -> None:
    logs.setup_logs(__name__)

    trio.run(chat)
