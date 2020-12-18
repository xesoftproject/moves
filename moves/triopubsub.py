from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import List, Dict, AsyncIterator, Generic, TypeVar, Any
import typing

import trio


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
            async for message in typing.cast(trio.MemoryReceiveChannel[Message[T]], r):
                yield message

    async def message(self, message: Message[T]) -> Message[T]:
        async with self.s.clone() as s:
            await typing.cast(trio.MemorySendChannel[Message[T]], s).send(message)
            return message

    async def aclose(self) -> None:
        await self.s.aclose()
        await self.r.aclose()


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
    send_old_messages: bool = True

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

        # send old messages
        if self.messages:
            for message in self.messages:
                await subscriber.message(message)
        else:
            await trio.sleep(0)

    async def aclose(self) -> None:
        if self.subscribers:
            for subscriber_id in self.subscribers:
                await self.subscribers[subscriber_id].aclose()
                del self.subscribers[subscriber_id]
        else:
            await trio.sleep(0)


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
        if subscription.send_old_messages and self.messages:
            for message in self.messages:
                await subscription.message(message)
        else:
            await trio.sleep(0)

        return subscription

    async def message(self, message: Message[T]) -> Message[T]:
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in self.subscriptions.values():
            await subscription.message(message)

        return message

    async def remove_subscription(self,
                                  subscription_id: str
                                  ) -> None:
        if subscription_id not in self.subscriptions:
            await trio.sleep(0)
            raise KeyError(f'{subscription_id}')

        await self.subscriptions[subscription_id].aclose()
        del self.subscriptions[subscription_id]


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
        if topic_id not in self.topics:
            await trio.sleep(0)
            raise KeyError(f'{topic_id}')
        if subscription.subscription_id in self.subscriptions:
            await trio.sleep(0)
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription
        return await self.topics[topic_id].add_subscription(subscription)

    async def send_message_to(self,
                              publisher: Publisher[T],
                              message: Message[T],
                              topic_id: str
                              ) -> Message[T]:
        if topic_id not in self.topics:
            await trio.sleep(0)
            raise KeyError(f'{topic_id}')

        return await publisher.send_message_to(message, self.topics[topic_id])

    async def subscribe(self,
                        subscriber: Subscriber[T],
                        subscription_id: str
                        ) -> AsyncIterator[Message[T]]:
        if subscription_id not in self.subscriptions:
            await trio.sleep(0)
            raise KeyError(f'{subscription_id}')

        subscription = self.subscriptions[subscription_id]
        async for message in subscriber.subscribe(subscription):
            yield message

    async def remove_subscription(self,
                                  topic_id: str,
                                  subscription_id: str
                                  ) -> None:
        if topic_id not in self.topics:
            await trio.sleep(0)
            raise KeyError(f'{topic_id}')
        if subscription_id not in self.subscriptions:
            await trio.sleep(0)
            raise KeyError(f'{subscription_id}')

        await self.topics[topic_id].remove_subscription(subscription_id)
        del self.subscriptions[subscription_id]
