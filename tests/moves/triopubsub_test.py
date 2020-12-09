import unittest

from moves import triopubsub

from .. import testssupport


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
        t1 = triopubsub.Topic('t1')
        t2 = triopubsub.Topic('t2')
        s1a = triopubsub.Subscription('s1a')
        s1b = triopubsub.Subscription('s1b')
        s2a = triopubsub.Subscription('s2a')
        s2b = triopubsub.Subscription('s2b')
        s2c = triopubsub.Subscription('s2c')

        # "statically" defined
        broker.add_topic(t1)
        broker.add_topic(t2)
        await broker.add_subscription(t1, s1a)
        await broker.add_subscription(t1, s1b)
        await broker.add_subscription(t2, s2a)
        await broker.add_subscription(t2, s2b)
        await broker.add_subscription(t2, s2c)

        # "dinamically" addedd / removed
        p1 = triopubsub.Publisher('p1')
        s1 = triopubsub.Subscriber('s1')

        m1 = triopubsub.Message('m1')
        m2 = triopubsub.Message('m2')
        m3 = triopubsub.Message('m3')

        await p1.send_message_to(m1, t1)
        await p1.send_message_to(m2, t1)
        await p1.send_message_to(m3, t1)

        acc = []
        async for message in s1.subscribe(s1a):
            acc.append(message)
            if message.message_id == 'm3':
                break

        self.assertEqual([m1, m2, m3], acc)
