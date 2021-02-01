from functools import wraps
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
from trio import run
from trio.abc import AsyncResource


_ = Any


def trio_test(afun: Callable[..., Awaitable[None]]) -> Callable[..., None]:
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
        for _ in range(n):
            acc.append(await aitor.__anext__())
        return acc
