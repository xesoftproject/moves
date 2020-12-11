from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, AsyncIterator, Generic, TypeVar, Any

import trio
import math

T = TypeVar('T')

@dataclass()
class Message(Generic[T]):
    message_id: str
    payload: T


@dataclass()
class Publisher(Generic[T]):
    publisher_id: str

    async def send_message_to(self,
                              message: Message[T],
                              topic: 'Topic[T]'
                              ) -> Message[T]:
        return await topic.message(message)


@dataclass()
class Subscriber(Generic[T]):
    subscriber_id: str
    s: trio.MemorySendChannel[Message[T]] = field(init=False)
    r: trio.MemoryReceiveChannel[Message[T]] = field(init=False)

    def __post_init__(self) -> None:
        s, r = trio.open_memory_channel[Message[T]](math.inf)
        self.s = s
        self.r = r

    async def subscribe(self,
                        subscription: 'Subscription[T]'
                        ) -> AsyncIterator[Message[T]]:
        await subscription.subscribe(self)
        async with self.r.clone() as r:
            async for message in r:
                yield message

    async def message(self, message: Message[T]) -> Message[T]:
        async with self.s.clone() as s:
            await s.send(message)
            return message


async def rr(d: Dict[str, T]) -> AsyncIterator[T]:
    while True:
        try:  # TODO: good enough?
            for value in d.values():
                yield value
        except RuntimeError:
            pass
        await trio.sleep(0)


@dataclass()
class Subscription(Generic[T]):
    subscription_id: str
    subscribers: Dict[str, Subscriber[T]] = field(default_factory=dict)
    rr: AsyncIterator[Subscriber[T]] = field(init=False)
    messages: List[Message[T]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.rr = rr(self.subscribers)

    async def message(self, message: Message[T]) -> Message[T]:
        self.messages.append(message)

        # ignore self if not subscribers
        if not self.subscribers:
            await trio.sleep(0)
            return message

        subscriber = await self.rr.__anext__()
        return await subscriber.message(message)

    async def subscribe(self, subscriber: Subscriber[T]) -> None:
        self.subscribers[subscriber.subscriber_id] = subscriber

        if not self.messages:
            await trio.sleep(0)

        # send old messages
        for message in self.messages:
            await subscriber.message(message)


@dataclass()
class Topic(Generic[T]):
    topic_id: str
    subscriptions: Dict[str, Subscription[T]] = field(default_factory=dict)
    messages: List[Message[T]] = field(default_factory=list)

    async def add_subscription(self,
                               subscription: Subscription[T]
                               ) -> Subscription[T]:
        if subscription.subscription_id in self.subscriptions:
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription

        # send old messages
        for message in self.messages:
            await subscription.message(message)

        return subscription

    async def message(self, message: Message[T]) -> Message[T]:
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in self.subscriptions.values():
            await subscription.message(message)

        return message


@dataclass()
class Broker:
    topics: Dict[str, Topic[Any]] = field(default_factory=dict)
    subscriptions: Dict[str, Subscription[Any]] = field(default_factory=dict)

    def add_topic(self, topic: Topic[T]) -> Topic[T]:
        if topic.topic_id in self.topics:
            raise KeyError(f'{topic.topic_id}')

        self.topics[topic.topic_id] = topic
        return topic

    async def add_subscription(self,
                               topic_id: str,
                               subscription: Subscription[T]
                               ) -> Subscription[T]:
        if subscription.subscription_id in self.subscriptions:
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription
        return await self.topics[topic_id].add_subscription(subscription)

    async def send_message_to(self,
                              publisher: Publisher[T],
                              message: Message[T],
                              topic_id: str
                              ) -> Message[T]:
        return await publisher.send_message_to(message, self.topics[topic_id])

    async def subscribe(self,
                        subscriber: Subscriber[T],
                        subscription_id: str
                        ) -> AsyncIterator[Message[T]]:
        subscription = self.subscriptions[subscription_id]
        async for message in subscriber.subscribe(subscription):
            yield message
