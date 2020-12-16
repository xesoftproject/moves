import unittest

from moves import triopubsub

from .. import testssupport
import trio
import typing


class TrioPubSubTest(unittest.TestCase):
    @testssupport.trio_test
    async def test_memory_topic(self) -> None:
        topic = triopubsub.Topic[str]('topic')
        subscription = triopubsub.Subscription[str]('subscription')
        message = triopubsub.Message[str]('message', 'payload')

        await topic.message(message)
        await topic.add_subscription(subscription)

        self.assertEqual([message], subscription.messages)

    @testssupport.trio_test
    async def test_memory_subscription(self) -> None:
        subscription = triopubsub.Subscription[None]('subscription')
        subscriber = triopubsub.Subscriber[None]('subscriber')
        message = triopubsub.Message[None]('message', None)

        await subscription.message(message)
        aitor = subscriber.subscribe(subscription)
        self.assertEqual(message, await testssupport.anext(aitor))

    @testssupport.trio_test
    async def test_rr(self) -> None:
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
    async def test_simple_flow(self) -> None:
        topic = triopubsub.Topic[int]('topic')
        subscription = triopubsub.Subscription[int]('subscription')
        subscriber = triopubsub.Subscriber[int]('subscriber')
        message = triopubsub.Message[int]('message', 123)
        await topic.add_subscription(subscription)
        aitor = subscriber.subscribe(subscription)
        await topic.message(message)
        self.assertEqual(message, await testssupport.anext(aitor))

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

        # "dinamically" addedd / removed
        p1 = triopubsub.Publisher[str]('p1')

        m1 = triopubsub.Message[str]('m1', 'payload1')
        m2 = triopubsub.Message[str]('m2', 'payload2')
        m3 = triopubsub.Message[str]('m3', 'payload3')

        await broker.send_message_to(p1, m1, 't1')
        await broker.send_message_to(p1, m2, 't1')
        await broker.send_message_to(p1, m3, 't1')

        acc = []
        async for message in broker.subscribe(triopubsub.Subscriber[str]('s1'),
                                              's1a'):
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
            async def get_first_message(subscriber: triopubsub.Subscriber[str],
                                        subscription_id: str
                                        ) -> None:
                async for message in broker.subscribe(subscriber, subscription_id):
                    acc[subscriber.subscriber_id] = message.message_id
                    break

            nursery.start_soon(get_first_message,
                               triopubsub.Subscriber[str]('subscriber1'),
                               'subscription1')
            nursery.start_soon(get_first_message,
                               triopubsub.Subscriber[str]('subscriber2'),
                               'subscription2')

            await trio.sleep(0)
            await broker.send_message_to(triopubsub.Publisher[str]('publisher'),
                                         triopubsub.Message[str]('message',
                                                                 'payload'),
                                         'topic')

        self.assertEqual({'subscriber1': 'message', 'subscriber2': 'message'},
                         acc)