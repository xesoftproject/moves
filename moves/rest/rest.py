from __future__ import annotations

import logging

import hypercorn.config
import hypercorn.trio
import quart
import quart_trio
import trio

from . import types
from .. import configurations


LOGS = logging.getLogger(__name__)


async def rest(input_send: trio.MemorySendChannel[types.InputQueueElement],
               output_receive: trio.MemoryReceiveChannel[types.OutputQueueElement]
               ) -> None:
    async with input_send, output_receive:
        LOGS.info('rest')

        config = hypercorn.config.Config()
        config.bind = [f'0.0.0.0:{configurations.REST_PORT}']

        app = quart_trio.QuartTrio(__name__)

        @app.route('/start_new_game', methods=['POST'])
        async def start_new_game():
            body = quart.request.json
            LOGS.info('start_new_game [body: %s]', body)

            # this is what should happen when a 'new game' endpoint is called
            # first example - cpu vs cpu
            input_ = types.InputQueueElement(command=types.Command.NEW_GAME,
                                             white=types.Player(player_id='cpu1',
                                                                player_type=types.PlayerType.CPU),
                                             black=types.Player(player_id='cpu2',
                                                                player_type=types.PlayerType.CPU))
            LOGS.info('start_new_game [input_: %s]', input_)

            await input_send.send(input_)

            async for output in output_receive:
                LOGS.info('start_new_game [output: %s]', output)
                if output.result != types.Result.GAME_CREATED:
                    continue
                game_id = output.game_universe.game_id
                return game_id

        @app.route('/update', methods=['POST'])
        def update():            # supposedly called by transcribe
            body = quart.request.json
            LOGS.info('start_new_game [body: {}]', body)

            game_id = body['game_id']
            move = body['move']

            input_ = types.InputQueueElement(command=types.Command.MOVE,
                                             game_id=game_id,
                                             move=move)

            app.nursery.start_soon(input_send.send, input_)
            LOGS.info('start_new_game [input_: {}]', input_)

            return input_

        await hypercorn.trio.serve(app, config)
