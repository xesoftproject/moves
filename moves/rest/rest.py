import logging

import trio


LOGS = logging.getLogger(__name__)


async def rest(input_send: trio.MemorySendChannel,
               output_receive: trio.MemoryReceiveChannel
               ) -> None:
    async with input_send, output_receive:
        raise NotImplementedError('make a rest server here')
