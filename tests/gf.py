from __future__ import annotations

import typing
import trio
import math


T = typing.TypeVar('T')


class Meta(type):
    def __getitem__(self: typing.Type[T], _) -> T:
        return self()


class gf(metaclass=Meta):
    def __call__(self) -> typing.Tuple[trio.MemorySendChannel[T],
                                       trio.MemoryReceiveChannel[T]]:
        return trio.open_memory_channel[T](math.inf)




async def main() -> None:
    reveal_type(gf)
    reveal_type(gf[str])
    reveal_type(gf[str]())

    a, b = gf[str]()
    await a.send('msg')
    async for msg in b:
        print(f'{msg=}')
        break

trio.run(main)
