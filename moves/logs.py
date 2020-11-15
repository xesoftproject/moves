import logging.config
import logging.handlers

from . import configurations


def _fqcn(cls: type) -> str:
    return f'{cls.__module__}.{cls.__qualname__}'

def setup_logs():
    if True or configurations.running_on_ec2():
        # write logs on file

        logging.config.dictConfig({
            'version': 1,
            'handlers': {
                'wsgi': {
                    'class': _fqcn(logging.handlers.TimedRotatingFileHandler),
                    'filename': f'logs/{__name__}.log',
                    'when': 'midnight',
                    'backupCount': 1
                }
            },
            'root': {
                'level': 'INFO',
                'handlers': ['wsgi']
            }
        })
