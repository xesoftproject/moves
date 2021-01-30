from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from math import inf
from typing import List, Dict, AsyncIterator, Generic, TypeVar, Any, cast, Type
from uuid import uuid4

from trio import open_memory_channel, sleep, MemoryReceiveChannel, MemorySendChannel


T = TypeVar('T')
Message = TypeVar('Message')


@dataclass()
class Subscription(Generic[Message]):
    subscription_id: str
    send_old_messages: bool = True
    s: MemorySendChannel[Message] = field(init=False)
    r: MemoryReceiveChannel[Message] = field(init=False)

    def __post_init__(self) -> None:
        self.s, self.r = open_memory_channel[Message](inf)

    async def message(self, message: Message) -> Message:
        async with self.s.clone() as s:
            await s.send(message)
        return message


@dataclass()
class Topic(Generic[Message]):
    topic_id: str
    subscriptions: Dict[str, Subscription[Message]
                        ] = field(default_factory=dict)
    messages: List[Message] = field(default_factory=list)

    async def add_subscription(self,
                               subscription: Subscription[Message]
                               ) -> Subscription[Message]:
        if subscription.subscription_id in self.subscriptions:
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription

        # send old messages
        if subscription.send_old_messages and self.messages:
            for message in self.messages:
                await subscription.message(message)
        else:
            await sleep(0)

        return subscription

    async def message(self, message: Message) -> Message:
        # save messages for future subscribers
        self.messages.append(message)

        for subscription in list(self.subscriptions.values()):
            await subscription.message(message)

        return message


@dataclass()
class Broker:
    topics: Dict[str, Topic[Any]] = field(default_factory=dict)
    subscriptions: Dict[str, Subscription[Any]] = field(default_factory=dict)

    def add_topic(self, topic: Topic[Message]) -> Topic[Message]:
        if topic.topic_id in self.topics:
            raise KeyError(f'{topic.topic_id}')

        self.topics[topic.topic_id] = topic
        return topic

    async def add_subscription(self,
                               topic_id: str,
                               subscription: Subscription[Message]
                               ) -> Subscription[Message]:
        if topic_id not in self.topics:
            await sleep(0)
            raise KeyError(f'{topic_id}')
        if subscription.subscription_id in self.subscriptions:
            await sleep(0)
            raise KeyError(f'{subscription.subscription_id}')

        self.subscriptions[subscription.subscription_id] = subscription
        return await self.topics[topic_id].add_subscription(subscription)

    async def send_message_to(self, message: Message, topic_id: str) -> Message:
        if topic_id not in self.topics:
            await sleep(0)
            raise KeyError(f'{topic_id}')

        return await cast(Topic[Message], self.topics[topic_id]).message(message)

    @asynccontextmanager
    async def with_tmp_subscription(self,
                                    topic_id: str,
                                    _cls: Type[Message],
                                    send_old_messages: bool = True
                                    ) -> AsyncIterator[Subscription[Message]]:
        if topic_id not in self.topics:
            await sleep(0)
            raise KeyError(f'{topic_id}')

        sub = await self.add_subscription(topic_id,
                                          Subscription[Message](str(uuid4()),
                                                                send_old_messages=send_old_messages))
        try:
            yield sub
        finally:
            del self.topics[topic_id].subscriptions[sub.subscription_id]

    async def messages(self,
                       subscription_id: str,
                       _cls: Type[Message],
                       ) -> AsyncIterator[Message]:
        if subscription_id not in self.subscriptions:
            await sleep(0)
            raise KeyError(f'{subscription_id}')

        subscription = self.subscriptions[subscription_id]
        async with subscription.r.clone() as r:
            async for message in r:
                yield message
