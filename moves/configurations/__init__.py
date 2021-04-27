import socket
import typing
import uuid


EC2_HOSTNAME = 'ip-172-31-36-240'


def running_on_ec2() -> bool:
    'detect if the code is running on aws or on local (dev) machines'

    return socket.gethostname() == EC2_HOSTNAME  # crude, but efficient


if running_on_ec2():
    from .aws import *
else:
    from .local import *

REST_PORT = 8443

__all__ = ['HOSTNAME',
           'REST_PORT',
           'STOCKFISH',
           'CERTFILE',
           'KEYFILE']
