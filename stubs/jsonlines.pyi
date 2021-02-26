from io import StringIO
from typing import Any
from typing import ContextManager
from typing import Iterable
from typing import Iterator
from typing import Literal
from typing import overload


class Reader(Iterable[Any], ContextManager['Reader']):
    def __init__(self, fn: StringIO) -> None: ...

    def __iter__(self) -> Iterator[Any]: ...


class Writer(ContextManager['Writer']):
    def __init__(self, fn: StringIO) -> None: ...

    def write(self, obj: Any) -> None: ...


@overload
def open(_fn: str, _mode: Literal['r'], / ) -> ContextManager[Reader]: ...


@overload
def open(_fn: str, _mode: Literal['a'], / ) -> ContextManager[Writer]: ...
