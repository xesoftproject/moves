import asyncio
import typing

T = typing.TypeVar('T')


def aio_as_trio(__proc: T) -> T:
    ...


def run(__afn: typing.Callable[[], typing.Awaitable[T]]) -> T:
    ...


def open_loop() -> typing.AsyncContextManager[asyncio.AbstractEventLoop]:
    ...
