from __future__ import annotations

import typing

import trio
from trio._util import generic_function


T = typing.TypeVar('T')


class MemorySendChannel(typing.Generic[T]):
    def __init__(self,
                 send_channels: typing.Iterable[trio.MemorySendChannel[T]]
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

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        for send_channel in self._send_channels:
            await send_channel.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        for send_channel in self._send_channels:
            await send_channel.aclose()


@generic_function
def open_memory_channel_tee(howmany: int = 2,
                            *args
                            ) -> typing.Tuple[MemorySendChannel[T], typing.List[trio.MemoryReceiveChannel[T]]]:
    output_sends: typing.List[trio.MemorySendChannel[T]] = []
    output_receives: typing.List[trio.MemoryReceiveChannel[T]] = []
    for _ in range(howmany):
        output_send, output_receive = trio.open_memory_channel[T](*args)
        output_sends.append(output_send)
        output_receives.append(output_receive)

    return (MemorySendChannel(output_sends), output_receives)
