from json import loads, dumps
from typing import cast, TypedDict

from hypercorn.config import Config
from hypercorn.trio import serve
from quart import websocket
from quart_cors import cors
from quart_trio import QuartTrio
from trio import run, open_nursery, sleep

from .configurations import CHAT_PORT, CERTFILE, KEYFILE
from .logs import setup_logs
from .triopubsub import Broker


class ChatMessage(TypedDict):
    from_: str
    body: str


async def mk_app() -> QuartTrio:
    # each "chat room" is a topic. for each connection there is a subscription
    # + there is a "chats" topic - with just the list of the topic_ids

    chats_topic_id = '__chats'

    broker = Broker()

    broker.add_topic(chats_topic_id, str)

    app = cast(QuartTrio, cors(QuartTrio(__name__),
                               # allow_origin='*',
                               allow_origin='http://localhost:8080',
                               allow_methods=['POST'],
                               allow_headers=['content-type']))

    @app.websocket('/chats')
    async def chats() -> None:
        'sync the currently open chats'

        await websocket.accept()

        async for chat_id in broker.subscribe_topic(chats_topic_id, str):
            await websocket.send(chat_id)

    @app.route('/chat/<string:chat_id>', methods=['POST'])
    async def create_chat(chat_id: str) -> str:
        'create a new chat'

        try:
            broker.add_topic(chat_id, ChatMessage)
        except KeyError:  # already present
            return chat_id

        await broker.send(chat_id, chats_topic_id)

        return chat_id

    @app.websocket('/chat/<string:chat_id>')
    async def chat(chat_id: str) -> None:
        'join a chat'

        async def send_messages(chat_id: str) -> None:
            message = await websocket.receive()
            await broker.send(loads(message), chat_id)

        async def receive_messages(chat_id: str) -> None:
            await sleep(0)
            await sleep(0)
            await sleep(0)
            await sleep(0)
            async for message in broker.subscribe_topic(chat_id, ChatMessage):
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

    await serve(await mk_app(), config)  # type: ignore


def main() -> None:
    setup_logs(__name__)

    run(chat)
