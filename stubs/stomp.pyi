import typing


class Connection:
    def __init__(self,
                 host_and_ports: typing.List[typing.Tuple[str, int]],
                 use_ssl: bool
                 ) -> None:
        ...

    def connect(self, username: str, passcode: str, wait: bool) -> None:
        ...

    def send(self, body: str, destination: str) -> None:
        ...
