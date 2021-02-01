from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from typing import List, Dict, AsyncIterator, Generic, TypeVar, Any, Type
from uuid import uuid4

from trio import open_memory_channel, MemoryReceiveChannel, MemorySendChannel


T = TypeVar('T')


@dataclass()
class Subscription(Generic[T]):
    subscription_id: str
    s: MemorySendChannel[T] = field(init=False)
    r: MemoryReceiveChannel[T] = field(init=False)

    def __post_init__(self) -> None:
        self.s, self.r = open_memory_channel[T](inf)

    async def send(self, message: T) -> None:
        async with self.s.clone() as s:
            return await s.send(message)

    async def subscribe(self) -> AsyncIterator[T]:
        async with self.r.clone() as r:
            async for message in r:
                yield message

    async def aclose(self) -> None:
        await self.s.aclose()
        await self.r.aclose()


@dataclass()
class Topic(Generic[T]):
    topic_id: str
    subscriptions: Dict[str, Subscription[T]] = field(default_factory=dict)
    messages: List[T] = field(default_factory=list)

    async def add_subscription(self,
                               subscription_id: str,
                               send_old_messages: bool) -> Subscription[T]:
        if subscription_id in self.subscriptions:
            raise KeyError(f'{subscription_id}')

        subscription = Subscription[T](subscription_id)
        self.subscriptions[subscription_id] = subscription

        # send old messages
        if send_old_messages and self.messages:
            for message in self.messages[:]:
                await subscription.send(message)

        return subscription

    async def remove_subscription(self,
                                  subscription_id: str)->None:
        subscription = self.subscriptions[subscription_id]
        await subscription.aclose()
        del self.subscriptions[subscription_id]

    async def send(self, message: T) -> T:
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in list(self.subscriptions.values()):
            await subscription.send(message)

        return message

    async def aclose(self) -> None:
        for subscription in self.subscriptions.values():
            await subscription.aclose()


@dataclass()
class Broker:
    topics: Dict[str, Topic[Any]] = field(default_factory=dict)
    subscriptions: Dict[str, Subscription[Any]] = field(default_factory=dict)

    async def add_topic(self, topic_id: str, _cls: Type[T]) -> Topic[T]:
        if topic_id in self.topics:
            raise KeyError(f'{topic_id}')

        topic = Topic[T](topic_id)
        self.topics[topic_id] = topic
        return topic

    async def add_subscription(self,
                               topic_id: str,
                               subscription_id: str,
                               send_old_messages: bool,
                               _cls: Type[T]) -> Subscription[T]:
        if topic_id not in self.topics:
            raise KeyError(f'{topic_id}')

        subscription = await self.topics[topic_id].add_subscription(subscription_id,
                                                                    send_old_messages)
        self.subscriptions[subscription_id] = subscription
        return subscription

    async def remove_subscription(self,
                                  topic_id: str,
                                  subscription_id: str) -> None:
        del self.subscriptions[subscription_id]
        await self.topics[topic_id].remove_subscription(subscription_id)

    async def remove_topic(self, topic_id: str) -> None:
        for subscription_id in list(self.topics[topic_id].subscriptions):
            await self.remove_subscription(topic_id, subscription_id)
        del self.topics[topic_id]

    async def send(self, message: T, topic_id: str) -> None:
        await self.topics[topic_id].send(message)

    async def subscribe(self,
                        subscription_id: str,
                        _cls: Type[T]) -> AsyncIterator[T]:
        async for message in self.subscriptions[subscription_id].subscribe():
            yield message

    async def subscribe_topic(self,
                              topic_id: str,
                              send_old_messages: bool,
                              _cls: Type[T]) -> AsyncIterator[T]:
        subscription_id = str(uuid4())

        subscription = await self.add_subscription(topic_id,
                                                   subscription_id,
                                                   send_old_messages,
                                                   _cls)
        try:
            async for message in self.subscribe(subscription_id, _cls):
                yield message
        finally:
            await self.remove_subscription(topic_id, subscription_id)
            subscription.aclose()

    async def aclose(self) -> None:
        for topic in self.topics.values():
            await topic.aclose()
