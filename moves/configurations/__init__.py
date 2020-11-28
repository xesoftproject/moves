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

# ws port (where the js consumer listen to)
WS_PORT = 61619

# stomp port (where the producer send messages)
STOMP_PORT = 61614

def amq_topic(game_id: str) -> str:
    'where you publish messages'

    return f'/topic/VirtualTopic.{game_id}'


def amq_queue(game_id: str, consumer_id: typing.Optional[str]= None) -> str:
    'what you subscribe on'
    if consumer_id is None:
        consumer_id = str(uuid.uuid4())

    return f'/queue/Consumer.{consumer_id}.VirtualTopic.{game_id}'


__all__ = ['WEB_PORT',
           'REST_PROTOCOL',
           'REST_HOSTNAME',
           'REST_PORT',
           'WS_PROTOCOL',
           'WS_PORT',
           'STOMP_PORT',
           'AMQ_HOSTNAME',
           'AMQ_USERNAME',
           'AMQ_PASSCODE',
           'STOCKFISH',
           'CERTFILE',
           'KEYFILE',
           'amq_topic',
           'amq_queue']
