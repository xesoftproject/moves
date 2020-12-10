import unittest

from moves import triopubsub

from .. import testssupport
import trio
import typing


class TrioPubSubTest(unittest.TestCase):
    @testssupport.trio_test
    async def test_memory_topic(self):
        topic = triopubsub.Topic('topic')
        subscription = triopubsub.Subscription('subscription')
        message = triopubsub.Message('message')

        await topic.message(message)
        await topic.add_subscription(subscription)

        self.assertEqual([message], subscription.messages)

    @testssupport.trio_test
    async def test_memory_subscription(self):
        subscription = triopubsub.Subscription('subscription')
        subscriber = triopubsub.Subscriber('subscriber')
        message = triopubsub.Message('message')

        await subscription.message(message)
        aitor = subscriber.subscribe(subscription)
        self.assertEqual(message, await testssupport.anext(aitor))

    @testssupport.trio_test
    async def test_rr(self):
        d = {'a': 1, 'b': 2}
        aitor = triopubsub.rr(d)
        self.assertEqual(1, await testssupport.anext(aitor))
        self.assertEqual(2, await testssupport.anext(aitor))
        self.assertEqual(1, await testssupport.anext(aitor))
        self.assertEqual(2, await testssupport.anext(aitor))
        self.assertEqual(1, await testssupport.anext(aitor))
        d['c'] = 3  # d modification
        self.assertEqual(1, await testssupport.anext(aitor))
        self.assertEqual(2, await testssupport.anext(aitor))
        self.assertEqual(3, await testssupport.anext(aitor))
        self.assertEqual(1, await testssupport.anext(aitor))
        self.assertEqual(2, await testssupport.anext(aitor))
        self.assertEqual(3, await testssupport.anext(aitor))
        self.assertEqual(1, await testssupport.anext(aitor))
        del d['b']  # d modification
        self.assertEqual(1, await testssupport.anext(aitor))
        self.assertEqual(3, await testssupport.anext(aitor))
        self.assertEqual(1, await testssupport.anext(aitor))
        self.assertEqual(3, await testssupport.anext(aitor))
        self.assertEqual(1, await testssupport.anext(aitor))

    @testssupport.trio_test
    async def test_simple_flow(self):
        topic = triopubsub.Topic('topic')
        subscription = triopubsub.Subscription('subscription')
        subscriber = triopubsub.Subscriber('subscriber')
        message = triopubsub.Message('message')
        await topic.add_subscription(subscription)
        aitor = subscriber.subscribe(subscription)
        await topic.message(message)
        self.assertEqual(message, await testssupport.anext(aitor))

    @testssupport.trio_test
    async def test_demo(self):
        broker = triopubsub.Broker()

        # "statically" defined
        broker.add_topic(triopubsub.Topic('t1'))
        broker.add_topic(triopubsub.Topic('t2'))
        await broker.add_subscription('t1', triopubsub.Subscription('s1a'))
        await broker.add_subscription('t1', triopubsub.Subscription('s1b'))
        await broker.add_subscription('t2', triopubsub.Subscription('s2a'))
        await broker.add_subscription('t2', triopubsub.Subscription('s2b'))
        await broker.add_subscription('t2', triopubsub.Subscription('s2c'))

        # "dinamically" addedd / removed
        p1 = triopubsub.Publisher('p1')

        m1 = triopubsub.Message('m1')
        m2 = triopubsub.Message('m2')
        m3 = triopubsub.Message('m3')

        await broker.send_message_to(p1, m1, 't1')
        await broker.send_message_to(p1, m2, 't1')
        await broker.send_message_to(p1, m3, 't1')

        acc = []
        async for message in broker.subscribe(triopubsub.Subscriber('s1'),
                                              's1a'):
            acc.append(message)
            if message is m3:
                break

        self.assertEqual([m1, m2, m3], acc)

    @testssupport.trio_test
    async def test_broadcast(self):
        broker = triopubsub.Broker()

        # "statically" defined
        broker.add_topic(triopubsub.Topic('topic'))
        await broker.add_subscription('topic',
                                      triopubsub.Subscription('subscription1'))
        await broker.add_subscription('topic',
                                      triopubsub.Subscription('subscription2'))

        acc: typing.Dict[str, str] = {}
        async with trio.open_nursery() as nursery:
            async def get_first_message(subscriber: triopubsub.Subscriber,
                                        subscription_id: str):
                async for message in broker.subscribe(subscriber, subscription_id):
                    acc[subscriber.subscriber_id] = message.message_id
                    break

            nursery.start_soon(get_first_message,
                               triopubsub.Subscriber('subscriber1'),
                               'subscription1')
            nursery.start_soon(get_first_message,
                               triopubsub.Subscriber('subscriber2'),
                               'subscription2')

            await trio.sleep(0)
            await broker.send_message_to(triopubsub.Publisher('publisher'),
                                         triopubsub.Message('message'),
                                         'topic')

        self.assertEqual({'subscriber1': 'message', 'subscriber2': 'message'},
                         acc)
