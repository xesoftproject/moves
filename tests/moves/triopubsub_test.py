import typing
import unittest

import trio

from moves import triopubsub

from .. import testssupport


class TrioPubSubTest(unittest.TestCase):
    @testssupport.trio_test
    async def test_memory_topic(self) -> None:
        topic = triopubsub.Topic[str]('topic')
        subscription = triopubsub.Subscription[str]('subscription')
        message = 'message'

        await topic.message(message)
        await topic.add_subscription(subscription)

        async with subscription.r.clone() as r:
            actual = await testssupport.anext(r)
        self.assertEqual(message, actual)

    @testssupport.trio_test
    async def test_demo(self) -> None:
        broker = triopubsub.Broker()

        # "statically" defined
        broker.add_topic(triopubsub.Topic('t1'))
        broker.add_topic(triopubsub.Topic('t2'))
        await broker.add_subscription('t1', triopubsub.Subscription('s1a'))
        await broker.add_subscription('t1', triopubsub.Subscription('s1b'))
        await broker.add_subscription('t2', triopubsub.Subscription('s2a'))
        await broker.add_subscription('t2', triopubsub.Subscription('s2b'))
        await broker.add_subscription('t2', triopubsub.Subscription('s2c'))

        m1 = 'payload1'
        m2 = 'payload2'
        m3 = 'payload3'

        await broker.send_message_to(m1, 't1')
        await broker.send_message_to(m2, 't1')
        await broker.send_message_to(m3, 't1')

        acc = []
        async for message in broker.messages('s1a', str):
            acc.append(message)
            if message is m3:
                break

        self.assertEqual([m1, m2, m3], acc)

    @testssupport.trio_test
    async def test_broadcast(self) -> None:
        broker = triopubsub.Broker()

        # "statically" defined
        broker.add_topic(triopubsub.Topic('topic'))
        await broker.add_subscription('topic',
                                      triopubsub.Subscription('subscription1'))
        await broker.add_subscription('topic',
                                      triopubsub.Subscription('subscription2'))

        acc: typing.Dict[str, str] = {}
        async with trio.open_nursery() as nursery:
            async def get_first_message(subscription_id: str) -> None:
                async for message in broker.messages(subscription_id, str):
                    acc[subscription_id] = message
                    break

            nursery.start_soon(get_first_message, 'subscription1')
            nursery.start_soon(get_first_message, 'subscription2')

            await trio.sleep(0)
            await broker.send_message_to('message', 'topic')

        self.assertEqual({'subscription1': 'message',
                          'subscription2': 'message'},
                         acc)

    @testssupport.trio_test
    async def test_order(self) -> None:
        broker = triopubsub.Broker()
        broker.add_topic(triopubsub.Topic[str]('t'))
        await broker.add_subscription('t', triopubsub.Subscription[str]('s'))

        messages1 = 'ABCDE'
        messages2 = '12345'

        async def producer1() -> None:
            for message in messages1:
                await broker.send_message_to(message, 't')

        async def producer2() -> None:
            for message in messages2:
                await broker.send_message_to(message, 't')

        accumulator = []

        async def consumer() -> None:
            i = 0
            async for message in broker.messages('s', str):
                accumulator.append(message)
                if i == len(messages1) + len(messages2) - 1:
                    break
                i += 1

        # "preload" the topic
        await producer1()
        async with trio.open_nursery() as nursery:
            # generates numbers
            nursery.start_soon(consumer)
            # consume letters and numbers (in this order)
            nursery.start_soon(producer2)

        self.assertListEqual(list(messages1 + messages2),
                             accumulator)
