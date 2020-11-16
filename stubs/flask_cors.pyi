import flask
import typing


class CORS:
    def __init__(self, flask: flask.Flask) -> None:
        ...


class cross_origin:
    def __init__(self) -> None:
        ...

    def __call__(self, fun: typing.Callable[[], str]) -> typing.Callable[[], str]:
        ...
