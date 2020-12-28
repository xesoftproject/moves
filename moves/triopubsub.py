from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from typing import List, Dict, AsyncIterator, Generic, TypeVar, Any, Set

from trio import open_memory_channel, sleep


T = TypeVar('T')
Message = TypeVar('Message')


class Publisher(Generic[Message]):
    async def send_message_to(self,
                              message: Message,
                              topic: 'Topic[Message]'
                              ) -> Message:
        return await topic.message(message)


class Subscriber(Generic[Message]):
    def __init__(self) -> None:
        s, r = open_memory_channel[Message](inf)
        self.s = s
        self.r = r

    async def subscribe(self,
                        subscription: 'Subscription[Message]'
                        ) -> AsyncIterator[Message]:
        await subscription.subscribe(self)
        async with self.r.clone() as r:
            async for message in r:
                yield message

    async def message(self, message: Message) -> Message:
        async with self.s.clone() as s:
            await s.send(message)
            return message

    async def aclose(self) -> None:
        await self.s.aclose()
        await self.r.aclose()


async def rr(ts: Set[T]) -> AsyncIterator[T]:
    while True:
        try:  # TODO: good enough?
            for t in ts:
                yield t
        except RuntimeError:
            pass
        await sleep(0)


@dataclass()
class Subscription(Generic[Message]):
    subscription_id: str
    subscribers: Set[Subscriber[Message]] = field(default_factory=set)
    rr: AsyncIterator[Subscriber[Message]] = field(init=False)
    messages: List[Message] = field(default_factory=list)
    send_old_messages: bool = True

    def __post_init__(self) -> None:
        self.rr = rr(self.subscribers)

    async def message(self, message: Message) -> Message:
        self.messages.append(message)

        # ignore self if not subscribers
        if not self.subscribers:
            await sleep(0)
            return message

        subscriber = await self.rr.__anext__()
        return await subscriber.message(message)

    async def subscribe(self, subscriber: Subscriber[Message]) -> None:
        self.subscribers.add(subscriber)

        # send old messages
        if self.messages:
            for message in self.messages:
                await subscriber.message(message)
        else:
            await sleep(0)

    async def aclose(self) -> None:
        if self.subscribers:
            for subscriber in list(self.subscribers):  # always loop on a copy
                await subscriber.aclose()
            self.subscribers.clear()
        else:
            await sleep(0)


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

    async def remove_subscription(self,
                                  subscription_id: str
                                  ) -> None:
        if subscription_id not in self.subscriptions:
            await sleep(0)
            raise KeyError(f'{subscription_id}')

        await self.subscriptions[subscription_id].aclose()
        del self.subscriptions[subscription_id]


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

    async def send_message_to(self,
                              publisher: Publisher[Message],
                              message: Message,
                              topic_id: str
                              ) -> Message:
        if topic_id not in self.topics:
            await sleep(0)
            raise KeyError(f'{topic_id}')

        return await publisher.send_message_to(message, self.topics[topic_id])

    async def subscribe(self,
                        subscriber: Subscriber[Message],
                        subscription_id: str
                        ) -> AsyncIterator[Message]:
        if subscription_id not in self.subscriptions:
            await sleep(0)
            raise KeyError(f'{subscription_id}')

        subscription = self.subscriptions[subscription_id]
        async for message in subscriber.subscribe(subscription):
            yield message

    async def remove_subscription(self,
                                  topic_id: str,
                                  subscription_id: str
                                  ) -> None:
        if topic_id not in self.topics:
            await sleep(0)
            raise KeyError(f'{topic_id}')
        if subscription_id not in self.subscriptions:
            await sleep(0)
            raise KeyError(f'{subscription_id}')

        await self.topics[topic_id].remove_subscription(subscription_id)
        del self.subscriptions[subscription_id]
