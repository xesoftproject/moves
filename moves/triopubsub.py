from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from math import inf
from typing import List, Dict, AsyncIterator, Generic, TypeVar, Any, Type
from uuid import uuid4

from trio import open_memory_channel, MemoryReceiveChannel, MemorySendChannel, sleep


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
        else:
            await sleep(0)

        return subscription

    async def remove_subscription(self, subscription_id: str)->None:
        await sleep(0)
        del self.subscriptions[subscription_id]

    async def send(self, message: T) -> T:
        # save messages for future subscribers
        self.messages.append(message)

        subscriptions = list(self.subscriptions.values())
        if subscriptions:
            for subscription in subscriptions:
                await subscription.send(message)
        else:
            await sleep(0)

        return message

    async def aclose(self) -> None:
        subscriptions = list(self.subscriptions.values())
        if subscriptions:
            for subscription in subscriptions:
                await subscription.aclose()
        else:
            await sleep(0)


@dataclass()
class Broker:
    topics: Dict[str, Topic[Any]] = field(default_factory=dict)
    subscriptions: Dict[str, Subscription[Any]] = field(default_factory=dict)

    async def add_topic(self, topic_id: str, _cls: Type[T]) -> Topic[T]:
        if topic_id in self.topics:
            raise KeyError(f'{topic_id}')

        await sleep(0)
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
        subscription_ids = list(self.topics[topic_id].subscriptions.keys())
        for subscription_id in subscription_ids:
            await self.remove_subscription(topic_id, subscription_id)
        else:
            await sleep(0)
        del self.topics[topic_id]

    async def send(self, message: T, topic_id: str) -> None:
        await self.topics[topic_id].send(message)

    async def subscribe(self,
                        subscription_id: str,
                        _cls: Type[T]) -> AsyncIterator[T]:
        async for message in self.subscriptions[subscription_id].subscribe():
            yield message

    @asynccontextmanager
    async def tmp_subscription(self,
                               topic_id: str,
                               send_old_messages: bool,
                               _cls: Type[T]) -> AsyncIterator[str]:
        subscription_id = str(uuid4())

        subscription = await self.add_subscription(topic_id,
                                                   subscription_id,
                                                   send_old_messages,
                                                   _cls)
        try:
            yield subscription_id
        finally:
            await self.remove_subscription(topic_id, subscription_id)
            await subscription.aclose()

    async def subscribe_topic(self,
                              topic_id: str,
                              send_old_messages: bool,
                              _cls: Type[T]) -> AsyncIterator[T]:
        async with self.tmp_subscription(topic_id,
                                         send_old_messages,
                                         _cls) as subscription_id:
            async for message in self.subscribe(subscription_id, _cls):
                yield message

    async def aclose(self) -> None:
        topics = list(self.topics.values())
        if topics:
            for topic in topics:
                await topic.aclose()
        else:
            await sleep(0)
