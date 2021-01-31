import typing
import unittest

import trio

from moves.triopubsub import Broker, Topic, Subscription

from ..testssupport import trio_test, anext, aenumerate, atake


class TrioPubSubTest(unittest.TestCase):
    @trio_test
    async def test_memory_true(self) -> None:
        broker = Broker()
        await broker.add_topic('topic', str)
        await broker.send('message', 'topic')
        await broker.add_subscription('topic', 'subscription', True, str)

        actual = await anext(broker.subscribe('subscription', str))
        self.assertEqual('message', actual)

    @trio_test
    async def test_demo(self) -> None:
        broker = Broker()

        # "statically" defined
        await broker.add_topic('t1', str)
        await broker.add_topic('t2', str)
        await broker.add_subscription('t1', 's1a', True, str)
        await broker.add_subscription('t1', 's1b', True, str)
        await broker.add_subscription('t2', 's2a', True, str)
        await broker.add_subscription('t2', 's2b', True, str)
        await broker.add_subscription('t2', 's2c', True, str)

        m1 = 'payload1'
        m2 = 'payload2'
        m3 = 'payload3'

        await broker.send(m1, 't1')
        await broker.send(m2, 't1')
        await broker.send(m3, 't1')

        actual = await atake(3, broker.subscribe('s1a', str))
        self.assertEqual([m1, m2, m3], actual)

    @trio_test
    async def test_broadcast(self) -> None:
        broker = Broker()

        # "statically" defined
        await broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription1', True, str)
        await broker.add_subscription('topic', 'subscription2', True, str)

        acc: typing.Dict[str, str] = {}
        async with trio.open_nursery() as nursery:
            async def get_first_message(subscription_id: str) -> None:
                messages = broker.subscribe(subscription_id, str)
                acc[subscription_id] = await anext(messages)

            nursery.start_soon(get_first_message, 'subscription1')
            nursery.start_soon(get_first_message, 'subscription2')

            await broker.send('message', 'topic')

        self.assertEqual({'subscription1': 'message',
                          'subscription2': 'message'},
                         acc)

    @trio_test
    async def test_order(self) -> None:
        broker = Broker()
        await broker.add_topic('t', str)
        await broker.add_subscription('t', 's', True, str)

        messages1 = 'ABCDE'
        messages2 = '12345'

        async def producer1() -> None:
            for message in messages1:
                await broker.send(message, 't')

        async def producer2() -> None:
            for message in messages2:
                await broker.send(message, 't')

        accumulator = []

        async def consumer() -> None:
            i = 0
            async for message in broker.subscribe('s', str):
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

    @trio_test
    async def test_aclose(self) -> None:
        broker = Broker()
        await broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription', True, str)
        await broker.aclose()
        with self.assertRaises(trio.ClosedResourceError):
            await broker.send('closed', 'topic')

    @trio_test
    async def test_add_remove(self) -> None:
        broker = Broker()

        topic = await broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription1', True, str)
        await broker.add_subscription('topic', 'subscription2', True, str)
        self.assertTrue('topic' in broker.topics)
        self.assertTrue('subscription1' in broker.subscriptions)
        self.assertTrue('subscription1' in topic.subscriptions)
        self.assertTrue('subscription2' in broker.subscriptions)
        self.assertTrue('subscription2' in topic.subscriptions)

        await broker.remove_subscription('topic', 'subscription1')
        self.assertTrue('topic' in broker.topics)
        self.assertFalse('subscription1' in broker.subscriptions)
        self.assertFalse('subscription1' in topic.subscriptions)
        self.assertTrue('subscription2' in broker.subscriptions)
        self.assertTrue('subscription2' in topic.subscriptions)

        await broker.remove_topic('topic')
        self.assertFalse('topic' in broker.topics)
        self.assertFalse('subscription1' in broker.subscriptions)
        self.assertFalse('subscription1' in topic.subscriptions)
        self.assertFalse('subscription2' in broker.subscriptions)
        self.assertFalse('subscription2' in topic.subscriptions)

    @trio_test
    async def test_add_keyerror(self) -> None:
        broker = Broker()
        await broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription', True, str)

        with self.assertRaises(KeyError):
            await broker.add_topic('topic', str)

        with self.assertRaises(KeyError):
            await broker.add_subscription('topic', 'subscription', True, str)

        with self.assertRaises(KeyError):
            await broker.add_subscription('XXX', 'subscription', True, str)

    @trio_test
    async def test_subscribe_topic(self) -> None:
        broker = Broker()
        await broker.add_topic('topic', int)
        for i in range(3):
            await broker.send(i, 'topic')
        actual = await atake(3, broker.subscribe_topic('topic', True, int))
        self.assertListEqual(list(range(3)), actual)
