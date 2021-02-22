import typing
from typing import Any
from typing import ContextManager
from typing import Iterable
from typing import Literal


class Writer:
    def write(self, obj: Any) -> None: ...


@typing.overload
def open(_fn: str, _mode: Literal['r'], /) -> ContextManager[Iterable[Any]]: ...


@typing.overload
def open(_fn: str, _mode: Literal['a'], /) -> ContextManager[Writer]: ...
