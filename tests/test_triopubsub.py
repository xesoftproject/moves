from typing import Dict
from typing import List
from unittest import TestCase

from trio import open_nursery

from moves.triopubsub import Broker

from ._support_for_tests import anext
from ._support_for_tests import atake
from ._support_for_tests import timeout
from ._support_for_tests import trio_test


class TestTriopubsub(TestCase):
    @trio_test
    @timeout(5)
    async def test_memory_true(self) -> None:
        broker = Broker()
        try:
            broker.add_topic('t', str)
            try:
                broker.send('m', 't')
                self.assertEqual('m',
                                 await anext(broker.subscribe_topic('t', str)))
            finally:
                await broker.remove_topic('t')
        finally:
            await broker.aclose()

    @trio_test
    @timeout(5)
    async def test_subscriptions_share_messages(self) -> None:
        broker = Broker()
        try:
            broker.add_topic('t', str)
            broker.add_subscription('t', 's1', str)
            broker.add_subscription('t', 's2', str)

            broker.send('m1', 't')
            broker.send('m2', 't')
            broker.send('m3', 't')

            self.assertListEqual(['m1', 'm2', 'm3'],
                                 await atake(3, broker.subscribe('t', 's1', str)))
            self.assertListEqual(['m1', 'm2', 'm3'],
                                 await atake(3, broker.subscribe('t', 's2', str)))
        finally:
            await broker.aclose()

    @trio_test
    @timeout(5)
    async def test_subscribe_in_nursery(self) -> None:
        broker = Broker()
        try:
            broker.add_topic('t', str)
            broker.add_subscription('t', 's1', str)
            broker.add_subscription('t', 's2', str)

            acc: Dict[str, str] = {}
            async with open_nursery() as nursery:
                async def get_m1() -> None:
                    acc['s1'] = await anext(broker.subscribe('t', 's1', str))

                async def get_m2() -> None:
                    acc['s2'] = await anext(broker.subscribe('t', 's2', str))

                nursery.start_soon(get_m1)
                nursery.start_soon(get_m2)

                broker.send('m', 't')

            self.assertDictEqual({'s1': 'm', 's2': 'm'}, acc)
        finally:
            await broker.aclose()

    @trio_test
    @timeout(5)
    async def test_order(self) -> None:
        ms1 = list('ABCDE')
        ms2 = list('12345')

        async def producer(broker: Broker, ms: List[str]) -> None:
            for m in ms:
                broker.send(m, 't')

        async def consumer(broker: Broker,
                           ms1: List[str], ms2: List[str],
                           s: str,
                           acc: List[str]) -> None:
            acc.extend(await atake(len(ms1) + len(ms2),
                                   broker.subscribe('t', s, str)))

        acc: List[str] = []

        broker = Broker()
        try:
            broker.add_topic('t', str)
            try:
                async with broker.tmp_subscription('t', str) as s:
                    # "preload" the topic
                    await producer(broker, ms1)
                    async with open_nursery() as nursery:
                        # generates numbers
                        nursery.start_soon(consumer, broker, ms1, ms2, s, acc)
                        # consume letters and numbers (in this order)
                        nursery.start_soon(producer, broker, ms2)

            finally:
                await broker.remove_topic('t')
        finally:
            await broker.aclose()

        self.assertListEqual(list(ms1 + ms2), acc)

    @trio_test
    @timeout(5)
    async def test_add_remove(self) -> None:
        broker = Broker()
        try:
            topic = broker.add_topic('topic', str)
            broker.add_subscription('topic', 'subscription1', str)
            broker.add_subscription('topic', 'subscription2', str)
            self.assertTrue('topic' in broker.topics)
            self.assertTrue('subscription1' in topic.subscriptions)
            self.assertTrue('subscription2' in topic.subscriptions)

            await broker.remove_subscription('topic', 'subscription1')
            self.assertTrue('topic' in broker.topics)
            self.assertFalse('subscription1' in topic.subscriptions)
            self.assertTrue('subscription2' in topic.subscriptions)

            await broker.remove_topic('topic')
            self.assertFalse('topic' in broker.topics)
            self.assertFalse('subscription1' in topic.subscriptions)
            self.assertFalse('subscription2' in topic.subscriptions)
        finally:
            await broker.aclose()

    @trio_test
    @timeout(5)
    async def test_add_keyerror(self) -> None:
        broker = Broker()
        broker.add_topic('topic', str)
        broker.add_subscription('topic', 'subscription', str)

        with self.assertRaises(KeyError):
            broker.add_topic('topic', str)

        with self.assertRaises(KeyError):
            broker.add_subscription('topic', 'subscription', str)

    @trio_test
    @timeout(5)
    async def test_sub_wait(self) -> None:
        async def producer(broker: Broker) -> None:
            broker.send('new1', 'topic')
            broker.send('new2', 'topic')

        async def consumer(broker: Broker, acc: List[str]) -> None:
            acc.extend(await atake(5,
                                   broker.subscribe_topic('topic', str)))

        acc: List[str] = []

        broker = Broker()
        broker.add_topic('topic', str)
        try:
            broker.send('old1', 'topic')
            broker.send('old2', 'topic')
            broker.send('old3', 'topic')

            async with open_nursery() as nursery:
                nursery.start_soon(producer, broker)
                nursery.start_soon(consumer, broker, acc)

        finally:
            await broker.remove_topic('topic')

        self.assertListEqual(['old1', 'old2', 'old3', 'new1', 'new2'],
                             acc)

    @trio_test
    @timeout(5)
    async def test_aclose(self) -> None:
        broker = Broker()
        try:
            broker.add_topic('foo', str)
            broker.send('msg', 'foo')
        finally:
            await broker.aclose()

        self.assertDictEqual({}, broker.topics)

    @trio_test
    @timeout(5)
    async def test_send_old_messages(self) -> None:
        b = Broker()
        try:
            b.add_topic('t', str)
            try:
                b.send('m1', 't')

                s1 = b.add_subscription('t', 's1', str,
                                        send_old_messages=False)
                try:
                    self.assertEqual(0, s1.s.statistics().current_buffer_used)
                    b.send('m2', 't')
                    self.assertEqual(1, s1.s.statistics().current_buffer_used)
                finally:
                    await b.remove_subscription('t', 's1')

                try:
                    s2 = b.add_subscription('t', 's2', str)
                    self.assertEqual(2, s2.s.statistics().current_buffer_used)
                finally:
                    await b.remove_subscription('t', 's2')
            finally:
                await b.remove_topic('t')
        finally:
            await b.aclose()
