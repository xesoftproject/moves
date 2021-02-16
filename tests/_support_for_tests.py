from functools import wraps
from sys import gettrace
from typing import Any
from typing import AsyncIterable
from typing import AsyncIterator
from typing import Awaitable
from typing import Callable
from typing import List
from typing import Tuple
from typing import TypeVar
from typing import cast

from async_generator import aclosing
from trio import fail_after
from trio import run
from trio import sleep
from trio.abc import AsyncResource

_ = Any

_AsyncTestMethod = Callable[..., Awaitable[None]]
_TestMethod = Callable[..., None]


def trio_test(afun: _AsyncTestMethod) -> _TestMethod:
    @wraps(afun)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        run(afun, *args, **kwargs)
    return wrapper


T = TypeVar('T')


async def anext(acloseable: AsyncIterable[T]) -> T:
    async with aclosing(cast(AsyncResource, acloseable)) as aiter:
        aitor = cast(AsyncIterable[T], aiter).__aiter__()
        return await aitor.__anext__()


async def aenumerate(aiter: AsyncIterable[T]) -> AsyncIterator[Tuple[int, T]]:
    i = 0
    async for e in aiter:
        yield i, e
        i += 1


async def atake(n: int, acloseable: AsyncIterable[T]) -> List[T]:
    async with aclosing(cast(AsyncResource, acloseable)) as aiter:
        aitor = cast(AsyncIterable[T], aiter).__aiter__()
        acc: List[T] = []
        if n <= 0:
            await sleep(0)
        for _ in range(n):
            acc.append(await aitor.__anext__())
        return acc


class timeout:
    def __init__(self, seconds: int=5) -> None:
        self.seconds = seconds
        if gettrace() is not None:
            self.seconds *= 100  # give me more time in debug

    def __call__(self, afun: _AsyncTestMethod) -> _AsyncTestMethod:
        @wraps(afun)
        async def wrapper(*args: Any, **kwargs: Any) -> None:
            with fail_after(self.seconds):
                return await afun(*args, **kwargs)
        return wrapper
