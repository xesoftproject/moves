from __future__ import annotations

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

    async def send_message_to(self,
                              message: Message,
                              topic: 'Topic'
                              ) -> Message:
        return await topic.message(message)


@dataclass()
class Subscriber:
    subscriber_id: str
    s: trio.MemorySendChannel[Message] = field(init=False)
    r: trio.MemoryReceiveChannel[Message] = field(init=False)

    def __post_init__(self):
        s, r = trio.open_memory_channel[Message](math.inf)
        self.s = s
        self.r = r

    async def subscribe(self,
                        subscription: 'Subscription'
                        ) -> AsyncIterator[Message]:
        await subscription.subscribe(self)
        async with self.r as r:
            async for message in r:
                yield message

    async def message(self, message: Message) -> Message:
        await self.s.send(message)
        return message


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
            return message

        subscriber = await self.rr.__anext__()
        return await subscriber.message(message)

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

    async def add_subscription(self,
                               subscription: Subscription
                               ) -> Subscription:
        if subscription.subscription_id in self.subscriptions:
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription

        # send old messages
        for message in self.messages:
            await subscription.message(message)

        return subscription

    async def message(self, message: Message) -> Message:
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in self.subscriptions.values():
            await subscription.message(message)

        return message


@dataclass()
class Broker:
    topics: Dict[str, Topic] = field(default_factory=dict)
    subscriptions: Dict[str, Subscription] = field(default_factory=dict)

    def add_topic(self, topic: Topic) -> Topic:
        if topic.topic_id in self.topics:
            raise KeyError(f'{topic.topic_id}')

        self.topics[topic.topic_id] = topic
        return topic

    async def add_subscription(self,
                               topic_id: str,
                               subscription: Subscription
                               ) -> Subscription:
        if subscription.subscription_id in self.subscriptions:
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription
        return await self.topics[topic_id].add_subscription(subscription)

    async def send_message_to(self,
                              publisher: Publisher,
                              message: Message,
                              topic_id: str
                              ) -> Message:
        return await publisher.send_message_to(message, self.topics[topic_id])

    async def subscribe(self,
                        subscriber: Subscriber,
                        subscription_id: str
                        ) -> AsyncIterator[Message]:
        subscription = self.subscriptions[subscription_id]
        async for message in subscriber.subscribe(subscription):
            yield message
