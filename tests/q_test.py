from typing import cast

from quart import websocket
from quart_cors import cors
from quart_trio import QuartTrio

from moves.triopubsub import Broker


async def mk_app() -> QuartTrio:
    broker = Broker()
    await broker.add_topic('topic', str)

    app = cast(QuartTrio, cors(QuartTrio(__name__),
                               allow_origin='*',
                               allow_methods=['POST'],
                               allow_headers=['content-type']))
    @app.websocket('/chats')
    async def foo() -> None:
        await websocket.accept()

        async for payload in broker.subscribe_topic('topic', True, str):
            await websocket.send(payload)

    @app.route('/chat/<string:payload>', methods=['POST'])
    async def bar(payload: str) -> str:
        await broker.send(payload, 'topic')
        return payload

    return app

