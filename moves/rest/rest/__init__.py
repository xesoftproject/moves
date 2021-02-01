from json import dumps
from logging import getLogger
from typing import cast

import hypercorn.config
import hypercorn.trio
import quart
import quart_cors
import quart_trio
import trio

from ..constants import INPUT_TOPIC, OUTPUT_TOPIC
from ... import configurations
from ...triopubsub import Topic, Subscription, Broker
from ..types import OutputQueueElement, Result
from .types import GamesOutput, StartNewGameInput, RegisterOutput, UpdateInput


LOGS = getLogger(__name__)


async def rest(broker: Broker) -> None:
    'rest/ws server, expose the game engine to users'

    # pub/sub "infrastructure"
    # TODO: move to a topic per game?
    subscription_id = __name__
    topic_games_id = 'games'

    await broker.add_subscription(OUTPUT_TOPIC,
                                  subscription_id,
                                  True,
                                  OutputQueueElement)

    await broker.add_topic(topic_games_id, str)

    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.REST_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    mk_app = cast(quart_trio.QuartTrio,
               quart_cors.cors(quart_trio.QuartTrio(__name__),
                               allow_origin='*',
                               allow_methods=['POST'],
                               allow_headers=['content-type']))

    @mk_app.route('/start_new_game', methods=['POST'])
    async def start_new_game() -> str:
        body = await quart.request.json
        LOGS.info('start_new_game [body: %s]', body)

        start_new_game_input = StartNewGameInput(**body)
        LOGS.info('start_new_game [start_new_game_input: %s]',
                  start_new_game_input)

        input_element = start_new_game_input.input_queue_element()
        LOGS.info('start_new_game [input_element: %s]', input_element)

        game_id = None

        # attach a "temporary" subscription to the topic to retrieve the
        # game_id
        # TODO: create a "id generator" topic/service/something?
        async def get_game_id() -> None:
            nonlocal game_id

            async for game_id_message in broker.subscribe_topic(OUTPUT_TOPIC,
                                                                False,
                                                                OutputQueueElement):
                output_element = game_id_message
                LOGS.info('output_element: %s', output_element)
                if output_element.result != Result.GAME_CREATED:
                    continue
                game_id = output_element.game_universe.game_id
                break

        async def send_start_game() -> None:
            await broker.send(input_element, INPUT_TOPIC)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(get_game_id)
            nursery.start_soon(send_start_game)

        if game_id is None:
            raise Exception('no game_id!')

        full = all([input_element.white is not None,
                    input_element.black is not None])

        await broker.send(GamesOutput('add', game_id, full=full),
                          topic_games_id)

        return game_id

    @mk_app.route('/update', methods=['POST'])
    async def update() -> str:            # supposedly called by transcribe
        body = quart.request.json
        LOGS.info('update [body: {}]', body)

        update_input = UpdateInput(**body)
        LOGS.info('update [update_input: {}]', update_input)

        input_element = update_input.input_queue_element()
        LOGS.info('update [input_element: {}]', input_element)

        await broker.send(input_element, INPUT_TOPIC)

        return str(input_element)

    @mk_app.websocket('/register/<string:game_id>')
    async def register(game_id: str) -> None:
        LOGS.info('register(%s)', game_id)

        async for output_element in broker.subscribe(subscription_id,
                                                     OutputQueueElement):
            LOGS.info('output_element: %s', output_element)

            if game_id != output_element.game_universe.game_id:
                continue

            register_output = RegisterOutput.from_output_queue_element(
                output_element)

            await quart.websocket.send(register_output.json())

    @mk_app.websocket('/games')
    async def games() -> None:
        LOGS.info('games()')

        async for games_output in broker.subscribe_topic(topic_games_id,
                                                         True,
                                                         GamesOutput):
            LOGS.info('games [games_output: %s]', games_output)

            await quart.websocket.send(games_output.json())

    await hypercorn.trio.serve(mk_app, config)
