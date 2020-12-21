import trio
import functools
import typing


def trio_test(afun: typing.Callable[..., typing.Awaitable[None]]
              ) -> typing.Callable[..., None]:
    @functools.wraps(afun)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> None:
        trio.run(afun, *args, **kwargs)
    return wrapper


T = typing.TypeVar('T')


async def anext(aitor: typing.AsyncIterator[T]) -> T:
    return await aitor.__anext__()
