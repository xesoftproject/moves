import functools
from typing import *

import trio


def trio_test(afun: Callable[..., Awaitable[None]]) -> Callable[..., None]:
    @functools.wraps(afun)
    def wrapper(*args: Any, **kwargs: Any) -> None:
        trio.run(afun, *args, **kwargs)
    return wrapper


T = TypeVar('T')


async def anext(aitor: AsyncIterator[T]) -> T:
    return await aitor.__anext__()


async def aenumerate(aiter: AsyncIterable[T]) -> AsyncIterable[Tuple[int, T]]:
    i = 0
    async for e in aiter:
        yield i, e
        i += 1


async def atake(n: int, aiter: AsyncIterable[T]) -> List[T]:
    aitor = aiter.__aiter__()
    acc: List[T] = []
    for _ in range(n):
        acc.append(await anext(aitor))
    return acc
