from typing import List
from unittest import TestCase

from quart_trio import QuartTrio
from trio import open_nursery

from moves.chat import mk_app

from ..testssupport import trio_test


class ChatTest(TestCase):
    @trio_test
    async def test_it_websocket(self) -> None:
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
