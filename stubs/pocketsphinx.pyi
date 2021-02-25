from typing import Iterable
from typing import Iterator


class LiveSpeech(Iterable[object]):
    def __init__(self, *,
                 verbose: bool = True,
                 hmm: str = '',
                 lm: str='',
                 dict: str='') -> None:
        ...

    def __iter__(self) -> Iterator[str]: ...


def get_model_path() -> str: ...
