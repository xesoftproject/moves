from __future__ import annotations

import logging
import typing

import hypercorn.config
import hypercorn.trio
import quart
import quart_cors
import quart_trio
import trio

from . import types
from .. import configurations
from .. import triopubsub
from . import constants
import json


LOGS = logging.getLogger(__name__)


async def rest(broker: triopubsub.Broker) -> None:
    'rest/ws server, expose the game engine to users'

    # pub/sub "infrastructure"
    subscription = triopubsub.Subscription[types.OutputQueueElement](__name__)
    # publisher can be reused
    publisher = triopubsub.Publisher[types.InputQueueElement](__name__)

    await broker.add_subscription(constants.OUTPUT_TOPIC, subscription)
    # TODO: move to a topic per game?

    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.REST_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    app = typing.cast(quart_trio.QuartTrio,
                      quart_cors.cors(quart_trio.QuartTrio(__name__),
                                      allow_origin='*',
                                      allow_methods=['POST'],
                                      allow_headers=['content-type']))

    @app.route('/start_new_game', methods=['POST'])
    async def start_new_game() -> typing.Optional[str]:
        body = await quart.request.json
        LOGS.info('start_new_game [body: %s]', body)

        game_id = None

        # attach a "temporary" subscription to the topic to retrieve the
        # game_id
        # TODO: create a "id generator" topic/service/something?
        async def get_game_id() -> None:
            game_id_subscription = await broker.add_subscription(constants.OUTPUT_TOPIC,
                                                                 triopubsub.Subscription[types.OutputQueueElement](f'{__name__}tmp',
                                                                                                                   send_old_messages=False))
            try:
                async for game_id_message in broker.subscribe(triopubsub.Subscriber[types.OutputQueueElement](__name__),
                                                              game_id_subscription.subscription_id):
                    output_element = game_id_message.payload
                    LOGS.info('output_element: %s', output_element)
                    if output_element.result != types.Result.GAME_CREATED:
                        continue
                    game_id = output_element.game_universe.game_id
                    break
            finally:
                await broker.remove_subscription(constants.OUTPUT_TOPIC,
                                                 game_id_subscription.subscription_id)

        async def send_start_game() -> None:
            # this is what should happen when a 'new game' endpoint is called
            # first example - cpu vs cpu
            input_element = types.InputQueueElement(command=types.Command.NEW_GAME,
                                                    white=types.Player(player_id='cpu1',
                                                                       player_type=types.PlayerType.CPU),
                                                    black=types.Player(player_id='cpu2',
                                                                       player_type=types.PlayerType.CPU))
            LOGS.info('start_new_game [input_element: %s]', input_element)
            message = triopubsub.Message[types.InputQueueElement](__name__,
                                                                  input_element)
            await broker.send_message_to(publisher, message, constants.INPUT_TOPIC)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(get_game_id)
            nursery.start_soon(send_start_game)

        return game_id

    @app.route('/update', methods=['POST'])
    def update() -> str:            # supposedly called by transcribe
        body = quart.request.json
        LOGS.info('start_new_game [body: {}]', body)

        game_id = body['game_id']
        move = body['move']

        input_element = types.InputQueueElement(command=types.Command.MOVE,
                                                game_id=game_id,
                                                move=move)
        message = triopubsub.Message[types.InputQueueElement](__name__,
                                                              input_element)

        app.nursery.start_soon(broker.send_message_to,
                               message,
                               constants.INPUT_TOPIC)
        LOGS.info('start_new_game [input_element: %s]', input_element)

        return str(input_element)

    @app.websocket('/register/<string:game_id>')
    async def register(game_id: str) -> None:
        LOGS.info('register(%s)', game_id)

        async for message in broker.subscribe(triopubsub.Subscriber[types.OutputQueueElement](__name__),
                                              subscription.subscription_id):
            output_element = message.payload
            LOGS.info('output_element: %s', output_element)

            if game_id != output_element.game_universe.game_id:
                continue

            body = json.dumps({
                'move': output_element.move,
                'table': str(output_element.game_universe.board)
            })
            await quart.websocket.send_channel(body)

    await hypercorn.trio.serve(app, config)
