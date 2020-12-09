from dataclasses import dataclass, field
from typing import List, Dict, AsyncIterator

import trio
import math


@dataclass()
class Message:
    message_id: str


@dataclass()
class Publisher:
    publisher_id: str

    async def send_message_to(self, message: Message, topic: 'Topic'):
        await topic.message(message)


@dataclass()
class Subscriber:
    subscriber_id: str
    s: trio.MemorySendChannel[Message] = field(init=False)
    r: trio.MemoryReceiveChannel[Message] = field(init=False)

    def __post_init__(self):
        s, r = trio.open_memory_channel[Message](math.inf)
        self.s = s
        self.r = r

    async def subscribe(self, subscription: 'Subscription') -> AsyncIterator[Message]:
        await subscription.subscribe(self)
        async with self.r as r:
            async for message in r:
                yield message

    async def message(self, message: Message):
        await self.s.send(message)


async def rr(d: Dict[str, Subscriber]) -> AsyncIterator[Subscriber]:
    while True:
        try:  # TODO: good enough?
            for value in d.values():
                yield value
        except RuntimeError:
            pass
        await trio.sleep(0)


@dataclass()
class Subscription:
    subscription_id: str
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)
    rr: AsyncIterator[Subscriber] = field(init=False)
    messages: List[Message] = field(default_factory=list)

    def __post_init__(self):
        self.rr = rr(self.subscribers)

    async def message(self, message: Message):
        self.messages.append(message)

        # ignore self if not subscribers
        if not self.subscribers:
            await trio.sleep(0)
        else:
            subscriber = await self.rr.__anext__()
            await subscriber.message(message)

    async def subscribe(self, subscriber: Subscriber):
        self.subscribers[subscriber.subscriber_id] = subscriber

        # send old messages
        for message in self.messages:
            await subscriber.message(message)


@dataclass()
class Topic:
    topic_id: str
    subscriptions: Dict[str, Subscription] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)

    def add_subscription(self, subscription: Subscription):
        self.subscriptions[subscription.subscription_id] = subscription

        # send old messages
        for message in self.messages:
            subscription.message(message)

    async def message(self, message: Message):
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in self.subscriptions.values():
            await subscription.message(message)


@dataclass()
class Broker:
    topics: Dict[str, Topic] = field(default_factory=dict)

    def add_topic(self, topic: Topic):
        self.topics[topic.topic_id] = topic

    def add_subscription(self, topic: Topic, subscription: Subscription):
        self.add_topic(topic)
        self.topics[topic.topic_id].add_subscription(subscription)


async def demo():
    broker = Broker()
    t1 = Topic('t1')
    t2 = Topic('t2')
    s1a = Subscription('s1a')
    s1b = Subscription('s1b')
    s2a = Subscription('s2a')
    s2b = Subscription('s2b')
    s2c = Subscription('s2c')

    # "statically" defined
    broker.add_topic(t1)
    broker.add_topic(t2)
    broker.add_subscription(t1, s1a)
    broker.add_subscription(t1, s1b)
    broker.add_subscription(t2, s2a)
    broker.add_subscription(t2, s2b)
    broker.add_subscription(t2, s2c)

    # "dinamically" addedd / removed
    p1 = Publisher('p1')
    s1 = Subscriber('s1')

    await p1.send_message_to(Message('m1'), t1)
    await p1.send_message_to(Message('m2'), t1)
    await p1.send_message_to(Message('m3'), t1)

    async for message in s1.subscribe(s1a):
        print(f'[{s1=}, {message=}]')
        if message.message_id == 'm3':
            break

trio.run(demo)
