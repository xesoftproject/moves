from logging import INFO
from logging import basicConfig
from logging.config import dictConfig
from logging.handlers import TimedRotatingFileHandler
from os import makedirs
from os.path import join

from .configurations import running_on_ec2


def _fqcn(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


LOGS_ROOT = 'logs'


def setup_logs(filename: str, running_on_ec2: bool=running_on_ec2()) -> None:
    if running_on_ec2:
        # write logs on file

        # ensure the directory exists
        makedirs(LOGS_ROOT, exist_ok=True)

        dictConfig({
            'version': 1,
            'handlers': {
                'wsgi': {
                    'class': _fqcn(TimedRotatingFileHandler),
                    'filename': join(LOGS_ROOT, filename),
                    'when': 'midnight',
                    'backupCount': 0
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['wsgi']
            }
        })
    else:
        basicConfig(level=INFO)
