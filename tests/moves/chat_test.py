from typing import List
from unittest import TestCase

from quart.testing.connections import TestWebsocketConnection
from quart_trio import QuartTrio
from trio import open_nursery

from moves.chat import mk_app

from ..testssupport import trio_test


class ChatTest(TestCase):
    @trio_test
    async def test_chats_websocket(self) -> None:
        async def producer(app: QuartTrio) -> None:
            client = app.test_client()
            await client.post('/chat/chat1')
            await client.post('/chat/chat2')

        acc: List[str] = []

        async def consumer(app: QuartTrio) -> None:
            client = app.test_client()
            async with client.websocket('/chats', headers={'Origin': '*'}) as ws:
                acc.append(await ws.receive())
                acc.append(await ws.receive())

        app = await mk_app()
        async with open_nursery() as nursery:
            nursery.start_soon(producer, app)
            nursery.start_soon(consumer, app)

        self.assertListEqual(['chat1', 'chat2'], acc)

    @trio_test
    async def test_chat_websocket_alone(self) -> None:
        async def producer(ws: TestWebsocketConnection) -> None:
            await ws.send('{"from_":"client","body":"foo"}')
            await ws.send('{"from_":"client","body":"bar"}')
            await ws.send('{"from_":"client","body":"baz"}')

        acc: List[str] = []

        async def consumer(ws: TestWebsocketConnection) -> None:
            acc.append(await ws.receive())
            acc.append(await ws.receive())
            acc.append(await ws.receive())

        app = await mk_app()
        client = app.test_client()  # only one client -> act as the browser?
        await client.post('/chat/c')  # create a chat
        async with client.websocket('/chat/c', headers={'Origin': '*'}) as ws:
            async with open_nursery() as nursery:
                nursery.start_soon(producer, ws)
                nursery.start_soon(consumer, ws)

        self.assertListEqual(['{"from_": "client", "body": "foo"}',
                              '{"from_": "client", "body": "bar"}',
                              '{"from_": "client", "body": "baz"}'],
                             acc)