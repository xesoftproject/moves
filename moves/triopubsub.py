from __future__ import annotations

from contextlib import asynccontextmanager
from math import inf
from typing import Any
from typing import AsyncIterable
from typing import AsyncIterator
from typing import Dict
from typing import Generic
from typing import List
from typing import Type
from typing import TypeVar
from typing import cast
from uuid import uuid4

from async_generator import aclosing
from trio import open_memory_channel
from trio import sleep
from trio.abc import AsyncResource

T = TypeVar('T')


class Subscription(Generic[T], AsyncResource):
    def __init__(self) -> None:
        self.s, self.r = open_memory_channel[T](inf)

#     async def send(self, message: T) -> None:
#         return await self.s.send(message)

    def _send_nowait(self, message: T) -> None:
        return self.s.send_nowait(message)

    async def subscribe(self) -> AsyncIterator[T]:
        async with self.r.clone() as r:
            async for message in r:
                yield message

    async def aclose(self) -> None:
        await self.s.aclose()
        await self.r.aclose()


class Topic(Generic[T], AsyncResource):
    def __init__(self) -> None:
        self.subscriptions: Dict[str, Subscription[T]] = {}
        self.messages: List[T] = []
        self.aclosing = False

    def add_subscription(self, subscription_id: str, *,
                         send_old_messages: bool=True) -> Subscription[T]:
        if self.aclosing:
            raise BrokenPipeError()
        if subscription_id in self.subscriptions:
            raise KeyError(subscription_id)

        subscription = Subscription[T]()

        # send old messages
        if send_old_messages:
            for message in list(self.messages):
                subscription._send_nowait(message)

        self.subscriptions[subscription_id] = subscription
        return subscription

    async def remove_subscription(self, subscription_id: str)->None:
        subscription = self.subscriptions[subscription_id]
        del self.subscriptions[subscription_id]
        await subscription.aclose()

    def send(self, message: T) -> None:
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in list(self.subscriptions.values()):
            subscription._send_nowait(message)

    async def aclose(self) -> None:
        self.aclosing = True
        subscription_ids = list(self.subscriptions.keys())
        if subscription_ids:
            for subscription_id in subscription_ids:
                await self.remove_subscription(subscription_id)
        else:
            await sleep(0)

        assert not self.subscriptions


class Broker(AsyncResource):
    def __init__(self) -> None:
        self.topics: Dict[str, Topic[Any]] = {}

    def add_topic(self, topic_id: str, _cls: Type[T]) -> Topic[T]:
        if topic_id in self.topics:
            raise KeyError(topic_id)

        topic = Topic[T]()
        self.topics[topic_id] = topic
        return topic

    def add_subscription(self, topic_id: str, subscription_id: str, _cls: Type[T], *,
                         send_old_messages: bool=True) -> Subscription[T]:
        return self.topics[topic_id].add_subscription(subscription_id,
                                                      send_old_messages=send_old_messages)

    async def remove_subscription(self, topic_id: str, subscription_id: str) -> None:
        await self.topics[topic_id].remove_subscription(subscription_id)

    async def remove_topic(self, topic_id: str) -> None:
        topic = self.topics[topic_id]
        del self.topics[topic_id]
        await topic.aclose()

    def send(self, message: T, topic_id: str) -> None:
        self.topics[topic_id].send(message)

    async def subscribe(self, topic_id: str, subscription_id: str, _cls: Type[T]) -> AsyncIterator[T]:
        async with aclosing(cast(AsyncResource,
                                 self.topics[topic_id].subscriptions[subscription_id].subscribe())) as aiter:
            async for message in cast(AsyncIterable[T], aiter):
                yield message

    @asynccontextmanager
    async def tmp_subscription(self, topic_id: str, _cls: Type[T], *,
                               send_old_messages: bool=True) -> AsyncIterator[str]:
        subscription_id = str(uuid4())

        self.add_subscription(topic_id, subscription_id, _cls,
                              send_old_messages=send_old_messages)
        try:
            yield subscription_id
        finally:
            await self.remove_subscription(topic_id, subscription_id)

    async def subscribe_topic(self, topic_id: str, _cls: Type[T], *,
                              send_old_messages: bool=True) -> AsyncIterator[T]:
        async with self.tmp_subscription(topic_id, _cls,
                                         send_old_messages=send_old_messages) as subscription_id:
            async with aclosing(cast(AsyncResource,
                                     self.subscribe(topic_id, subscription_id, _cls))) as aiter:
                async for message in cast(AsyncIterable[T], aiter):
                    yield message

    async def aclose(self) -> None:
        topic_ids = list(self.topics.keys())
        if topic_ids:
            for topic_id in topic_ids:
                await self.remove_topic(topic_id)
        else:
            await sleep(0)
