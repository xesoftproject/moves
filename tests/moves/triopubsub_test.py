from __future__ import annotations

from typing import Dict, List
from unittest import TestCase

from trio import open_nursery, sleep

from moves.triopubsub import Broker

from ..testssupport import trio_test, anext, atake


class TrioPubSubTest(TestCase):
    @trio_test
    async def test_memory_true(self) -> None:
        broker = Broker()
        broker.add_topic('topic', str)
        await broker.send('message', 'topic')
        await broker.add_subscription('topic', 'subscription',  str)

        a = broker.subscribe('subscription', str)
        actual = await anext(a)
        self.assertEqual('message', actual)

    @trio_test
    async def test_demo(self) -> None:
        broker = Broker()

        # "statically" defined
        broker.add_topic('t1', str)
        broker.add_topic('t2', str)
        await broker.add_subscription('t1', 's1a',  str)
        await broker.add_subscription('t1', 's1b',  str)
        await broker.add_subscription('t2', 's2a',  str)
        await broker.add_subscription('t2', 's2b',  str)
        await broker.add_subscription('t2', 's2c',  str)

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
        broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription1',  str)
        await broker.add_subscription('topic', 'subscription2',  str)

        acc: Dict[str, str] = {}
        async with open_nursery() as nursery:
            async def get_first_message(subscription_id: str) -> None:
                acc[subscription_id] = await anext(broker.subscribe(subscription_id, str))

            nursery.start_soon(get_first_message, 'subscription1')
            nursery.start_soon(get_first_message, 'subscription2')

            await broker.send('message', 'topic')

        self.assertEqual({'subscription1': 'message',
                          'subscription2': 'message'},
                         acc)

    @trio_test
    async def test_order(self) -> None:
        broker = Broker()
        broker.add_topic('t', str)
        await broker.add_subscription('t', 's',  str)

        messages1 = 'ABCDE'
        messages2 = '12345'

        async def producer1() -> None:
            for message in messages1:
                await broker.send(message, 't')

        async def producer2() -> None:
            for message in messages2:
                await broker.send(message, 't')

        accumulator: List[str] = []

        async def consumer() -> None:
            accumulator.extend(await atake(len(messages1) + len(messages2),
                                           broker.subscribe('s', str)))

        # "preload" the topic
        await producer1()
        async with open_nursery() as nursery:
            # generates numbers
            nursery.start_soon(consumer)
            # consume letters and numbers (in this order)
            nursery.start_soon(producer2)

        self.assertListEqual(list(messages1 + messages2),
                             accumulator)

    @trio_test
    async def test_add_remove(self) -> None:
        broker = Broker()

        topic = broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription1',  str)
        await broker.add_subscription('topic', 'subscription2',  str)
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
        broker.add_topic('topic', str)
        await broker.add_subscription('topic', 'subscription',  str)

        with self.assertRaises(KeyError):
            broker.add_topic('topic', str)

        with self.assertRaises(KeyError):
            await broker.add_subscription('topic', 'subscription',  str)

        with self.assertRaises(KeyError):
            await broker.add_subscription('XXX', 'subscription',  str)

    @trio_test
    async def test_subscribe_topic(self) -> None:
        broker = Broker()
        broker.add_topic('topic', int)
        for i in range(3):
            await broker.send(i, 'topic')
        actual = await atake(3, broker.subscribe_topic('topic', int))
        self.assertListEqual(list(range(3)), actual)

    @trio_test
    async def test_sub_wait(self) -> None:
        broker = Broker()
        broker.add_topic('topic', str)
        await broker.send('old1', 'topic')
        await broker.send('old2', 'topic')
        await broker.send('old3', 'topic')

        async def producer() -> None:
            await broker.send('new1', 'topic')
            await broker.send('new2', 'topic')

        accumulator: List[str] = []

        async def consumer() -> None:
            await sleep(0)
            await sleep(0)
            accumulator.extend(await atake(5,
                                           broker.subscribe_topic('topic', str)))

        async with open_nursery() as nursery:
            nursery.start_soon(producer)
            nursery.start_soon(consumer)

        self.assertListEqual(['old1', 'old2', 'old3', 'new1', 'new2'],
                             accumulator)
