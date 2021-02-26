from json import dumps
from json import loads
from logging import getLogger
from typing import TypedDict
from typing import cast

from async_generator import aclosing
from hypercorn.config import Config
from hypercorn.trio import serve
from quart import websocket
from quart_cors import cors
from quart_trio import QuartTrio
from trio import open_nursery
from trio import run

from .configurations import CERTFILE
from .configurations import CHAT_PORT
from .configurations import HOSTNAME
from .configurations import HTTP
from .configurations import KEYFILE
from .configurations import WEB_PORT
from .logs import setup_logs
from .rest.storage import load_broker
from .triopubsub import Broker

setup_logs(__name__)
LOGS = getLogger(__name__)


class ChatMessage(TypedDict):
    from_: str
    body: str


async def mk_app(broker: Broker) -> QuartTrio:
    # each "chat room" is a topic. for each connection there is a subscription
    # + there is a "chats" topic - with just the list of the topic_ids

    chats_topic_id = '__chats'

    broker.add_topic(chats_topic_id, str)

    allow_origin = (f'{HTTP}://{HOSTNAME}'
                    if ((HTTP == 'http' and WEB_PORT == 80)
                        or (HTTP == 'https' and WEB_PORT == 443))
                    else f'{HTTP}://{HOSTNAME}:{WEB_PORT}')

    app = cast(QuartTrio, cors(QuartTrio(__name__),
                               allow_origin=allow_origin,
                               allow_methods=['POST'],
                               allow_headers=['content-type']))

    @app.websocket('/chats')
    async def chats() -> None:
        'sync the currently open chats'

        await websocket.accept()

        async with aclosing(broker.subscribe_topic(chats_topic_id,
                                                   str)) as chat_ids:  # type: ignore
            async for chat_id in chat_ids:
                if chat_id not in broker.topics: # should be here?
                    broker.add_topic(chat_id, ChatMessage)
                await websocket.send(chat_id)

    @app.route('/chat/<string:chat_id>', methods=['POST'])
    async def create_chat(chat_id: str) -> str:
        'create a new chat'

        try:
            broker.add_topic(chat_id, ChatMessage)
        except KeyError:  # already present
            return chat_id

        broker.send(chat_id, chats_topic_id)

        return chat_id

    @app.websocket('/chat/<string:chat_id>')
    async def chat(chat_id: str) -> None:
        'join a chat'

        async def receive_messages(chat_id: str) -> None:
            while True:
                message = await websocket.receive()
                broker.send(loads(message), chat_id)

        async def send_messages(chat_id: str) -> None:
            async with aclosing(broker.subscribe_topic(chat_id,
                                                       ChatMessage)) as messages:  # type: ignore
                async for message in messages:
                    await websocket.send(dumps(message))

        async with open_nursery() as nursery:
            await websocket.accept()
            nursery.start_soon(send_messages, chat_id)
            nursery.start_soon(receive_messages, chat_id)

    return app


async def chat() -> None:
    config = Config()
    config.bind = [f'0.0.0.0:{CHAT_PORT}']
    if CERTFILE:
        config.certfile = CERTFILE
    if KEYFILE:
        config.keyfile = KEYFILE

    await serve(await mk_app(load_broker()), config)  # type: ignore


def main() -> None:
    run(chat)
