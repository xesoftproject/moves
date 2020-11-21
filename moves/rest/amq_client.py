from __future__ import annotations

import json
import logging

import stomp
import trio

from . import types
from .. import configurations


LOGS = logging.getLogger(__name__)


async def amq_client(output_receive: trio.MemoryReceiveChannel[types.OutputQueueElement]
                     ) -> None:
    async with output_receive:
        LOGS.info('amq_client')

        conn = stomp.Connection([(configurations.AMQ_HOSTNAME,
                                  configurations.STOMP_PORT)])
        conn.set_ssl([(configurations.AMQ_HOSTNAME, configurations.STOMP_PORT)])
        conn.connect(configurations.AMQ_USERNAME,
                     configurations.AMQ_PASSCODE,
                     wait=True)

        async for output_element in output_receive:
            LOGS.info('output_element: %s', output_element)

            body = json.dumps({
                'move': output_element.move,
                'table': str(output_element.game_universe.board)
            })
            destination = f'/topic/{configurations.AMQ_QUEUE}-{output_element.game_universe.game_id}'

            conn.send(body=body, destination=destination)
