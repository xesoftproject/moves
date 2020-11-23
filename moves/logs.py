import logging.config
import logging.handlers
import os

from . import configurations


def _fqcn(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'


LOGS_ROOT = 'logs'


def setup_logs() -> None:
    if configurations.running_on_ec2():
        # write logs on file

        # ensure the directory exists
        os.makedirs(LOGS_ROOT, exist_ok=True)

        logging.config.dictConfig({
            'version': 1,
            'handlers': {
                'wsgi': {
                    'class': _fqcn(logging.handlers.TimedRotatingFileHandler),
                    'filename': f'{LOGS_ROOT}/{__name__}',
                    'when': 'midnight',
                    'backupCount': 1
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['wsgi']
            }
        })
