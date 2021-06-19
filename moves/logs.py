from logging import DEBUG
from logging import INFO
from logging import StreamHandler
from logging import basicConfig
from logging.handlers import TimedRotatingFileHandler
from os import makedirs
from os.path import join
from sys import stdout

from .configurations import running_on_ec2


def _fqcn(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


LOGS_ROOT = 'logs'

_SETUP_DONE = False


def setup_logs(filename: str, running_on_ec2: bool = running_on_ec2()) -> None:
    global _SETUP_DONE
    if _SETUP_DONE:
        return
    _SETUP_DONE = True

    if running_on_ec2:
        # write logs on file

        # ensure the directory exists
        makedirs(LOGS_ROOT, exist_ok=True)

        basicConfig(
            level=DEBUG,
            handlers=[
                StreamHandler(stdout),
                TimedRotatingFileHandler(
                    join(
                        LOGS_ROOT,
                        filename),
                    when='midnight')],
            force=True)
    else:
        basicConfig(level=INFO,
                    handlers=[StreamHandler(stdout)],
                    force=True)
