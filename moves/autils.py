from __future__ import annotations

import types
import typing

import trio


T = typing.TypeVar('T')


class MemorySendChannel(typing.Generic[T]):
    def __init__(self,
                 send_channels: typing.List[trio.MemorySendChannel[T]]
                 ) -> None:
        self._send_channels = send_channels

    def clone(self) -> 'MemorySendChannel[T]':
        return MemorySendChannel[T]([send_channel.clone()
                                     for send_channel in self._send_channels])

    async def send(self, value: T) -> None:
        for send_channel in self._send_channels:
            await send_channel.send(value)

    async def __aenter__(self) -> 'MemorySendChannel[T]':
        return MemorySendChannel[T]([await send_channel.__aenter__()
                                     for send_channel in self._send_channels])

    async def __aexit__(self,
                        exc_type: typing.Type[Exception],
                        exc_value: Exception,
                        traceback: types.TracebackType
                        ) -> None:
        for send_channel in reversed(self._send_channels):
            await send_channel.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        for send_channel in self._send_channels:
            await send_channel.aclose()


class _OpenMemoryChannelTeeMeta(type):
    def __getitem__(self: typing.Callable[[], typing.Callable[[int, float], typing.Tuple[MemorySendChannel[T], typing.List[trio.MemoryReceiveChannel[T]]]]],
                    _: typing.Type[T]
                    ) -> typing.Callable[[int, float], typing.Tuple[MemorySendChannel[T], typing.List[trio.MemoryReceiveChannel[T]]]]:
        return self()


class open_memory_channel_tee(metaclass=_OpenMemoryChannelTeeMeta):
    def __call__(self,
                 howmany: int,
                 max_buffer_size: float
                 ) -> typing.Tuple[MemorySendChannel[T], typing.List[trio.MemoryReceiveChannel[T]]]:
        output_sends: typing.List[trio.MemorySendChannel[T]] = []
        output_receives: typing.List[trio.MemoryReceiveChannel[T]] = []
        for _ in range(howmany):
            output_send, output_receive = trio.open_memory_channel[T](
                max_buffer_size)
            output_sends.append(output_send)
            output_receives.append(output_receive)

        return MemorySendChannel[T](output_sends), output_receives


class Msc(typing.Generic[T]):
    def __init__(self,
                 max_buffer_size: float,
                 send_channels: typing.List[trio.MemorySendChannel[T]] = None):
        self._max_buffer_size = max_buffer_size
        self._send_channels = send_channels or []

    def fork(self) -> trio.MemoryReceiveChannel:
        send, receive = trio.open_memory_channel[T](self._max_buffer_size)
        self._send_channels.append(send)
        return receive

    def clone(self) -> 'Msc[T]':
        return Msc[T](self._max_buffer_size,
                      [channel.clone() for channel in self._send_channels])

    async def send(self, value: T) -> None:
        for channel in self._send_channels:
            await channel.send(value)

    async def __aenter__(self) -> 'Msc[T]':
        return Msc[T](self._max_buffer_size,
                      [await channel.__aenter__() for channel in self._send_channels])

    async def __aexit__(self,
                        exc_type: typing.Type[Exception],
                        exc_value: Exception,
                        traceback: types.TracebackType
                        ) -> None:
        for channel in reversed(self._send_channels):
            await channel.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        for channel in reversed(self._send_channels):
            await channel.aclose()
