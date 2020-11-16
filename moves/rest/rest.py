from __future__ import annotations

import logging

import trio

from . import types


LOGS = logging.getLogger(__name__)

async def rest(input_send: trio.MemorySendChannel[types.InputQueueElement]
               ) -> None:
    async with input_send:
        LOGS.info('rest')

        # TODO: make a *real* rest server

        # this is what should happen when a "new game" endpoint is called
        # first example - cpu vs cpu
        demo = types.InputQueueElement(command=types.Command.NEW_GAME,
                                       white=types.Player(player_id='cpu1',
                                                          player_type=types.PlayerType.CPU),
                                       black=types.Player(player_id='cpu2',
                                                          player_type=types.PlayerType.CPU))

        await input_send.send(demo)
