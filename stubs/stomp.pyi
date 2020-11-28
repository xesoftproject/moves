import typing


class Connection:
    def __init__(self,
                 host_and_ports: typing.List[typing.Tuple[str, int]]
                 ) -> None:
        ...

    def set_ssl(self,
                host_and_ports: typing.List[typing.Tuple[str, int]]
                ) -> None:
        ...

    def connect(self, username: str, passcode: str, wait: bool) -> None:
        ...

    def send(self,
             destination: str,
             body: str,
             content_type: typing.Optional[str]=None
             ) -> None:
        ...
