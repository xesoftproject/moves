import json
import logging

import stomp
import trio

from .. import configurations


LOGS = logging.getLogger(__name__)


async def amq_client(output_queue: trio.MemoryReceiveChannel) -> None:
    conn = stomp.Connection([(configurations.AMQ_HOSTNAME,
                              configurations.STOMP_PORT)],
                            use_ssl=True)
    conn.connect(configurations.AMQ_USERNAME,
                 configurations.AMQ_PASSCODE, wait=True)

    async with output_queue:
        async for response in output_queue:
            LOGS.info('response: %s', response)

            body = json.dumps({
                'move': response.move,
                'table': str(response.board)
            })
            destination = f'/topic/{configurations.AMQ_QUEUE}-{response.game_id}'

            conn.send(body=body, destination=destination)
