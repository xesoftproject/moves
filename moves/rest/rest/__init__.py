from logging import getLogger
from typing import cast

from async_generator import aclosing
from hypercorn.config import Config
from hypercorn.trio import serve
from quart import request
from quart import websocket
from quart_cors import cors
from quart_trio import QuartTrio
from trio import open_nursery

from ...configurations import CERTFILE
from ...configurations import HOSTNAME
from ...configurations import HTTP
from ...configurations import KEYFILE
from ...configurations import REST_PORT
from ...configurations import WEB_PORT
from ...triopubsub import Broker
from ..constants import INPUT_TOPIC
from ..constants import OUTPUT_TOPIC
from ..types import OutputQueueElement
from ..types import Result
from .types import GamesOutput
from .types import RegisterOutput
from .types import StartNewGameInput
from .types import UpdateInput

LOGS = getLogger(__name__)


async def mk_app(broker: Broker) -> QuartTrio:
    # pub/sub "infrastructure"
    topic_games_id = 'games'

    broker.add_topic(topic_games_id, str)

    allow_origin = (f'{HTTP}://{HOSTNAME}'
                    if ((HTTP == 'http' and WEB_PORT == 80)
                        or (HTTP == 'https' and WEB_PORT == 443))
                    else f'{HTTP}://{HOSTNAME}')

    app = cast(QuartTrio, cors(QuartTrio(__name__),
                               allow_origin=allow_origin,
                               allow_methods=['POST'],
                               allow_headers=['content-type']))

    @app.websocket('/games')
    async def games() -> None:
        LOGS.info('games()')

        await websocket.accept()

        async with aclosing(broker.subscribe_topic(topic_games_id,
                                                   GamesOutput)) as games_outputs:  # type: ignore
            async for games_output in games_outputs:
                LOGS.info('games [games_output: %s]', games_output)
                await websocket.send(games_output.json())

    @app.route('/start_new_game', methods=['POST'])
    async def start_new_game() -> str:
        body = await request.json
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

            async with aclosing(broker.subscribe_topic(OUTPUT_TOPIC,
                                                       OutputQueueElement,
                                                       send_old_messages=False)) as game_id_messages:  # type: ignore
                async for game_id_message in game_id_messages:
                    output_element = game_id_message
                    LOGS.info('output_element: %s', output_element)
                    if output_element.result != Result.GAME_CREATED:
                        continue
                    game_id = output_element.game_universe.game_id
                    break

        async def send_start_game() -> None:
            broker.send(input_element, INPUT_TOPIC)

        async with open_nursery() as nursery:
            nursery.start_soon(get_game_id)
            nursery.start_soon(send_start_game)

        if game_id is None:
            raise Exception('no game_id!')

        full = all([input_element.white is not None,
                    input_element.black is not None])

        broker.send(GamesOutput('add', game_id, full=full), topic_games_id)

        return game_id

    @app.websocket('/register_on_send/<string:game_id>')
    async def register_on_send(game_id: str) -> None:
        getLogger('VITO').info('register_on_send(%s)', game_id)

        await websocket.accept()

        async with aclosing(broker.subscribe_topic(OUTPUT_TOPIC,
                                                   OutputQueueElement)) as output_elements:  # type: ignore
            async for output_element in output_elements:
                getLogger('VITO').info('output_element: %s',
                                       output_element.move)

                if game_id != output_element.game_universe.game_id:
                    continue

                register_output = RegisterOutput.from_output_queue_element(
                    output_element)

                await websocket.send(register_output.json())

    @app.route('/update', methods=['POST'])
    async def update() -> str:            # supposedly called by transcribe
        body = request.json
        LOGS.info('update [body: {}]', body)

        update_input = UpdateInput(**body)
        LOGS.info('update [update_input: {}]', update_input)

        input_element = update_input.input_queue_element()
        LOGS.info('update [input_element: {}]', input_element)

        broker.send(input_element, INPUT_TOPIC)

        return str(input_element)

    return app


async def rest(broker: Broker) -> None:
    'rest/ws server, expose the game engine to users'

    config = Config()
    config.bind = [f'0.0.0.0:{REST_PORT}']
    if CERTFILE:
        config.certfile = CERTFILE
    if KEYFILE:
        config.keyfile = KEYFILE

    await serve(await mk_app(broker), config)  # type: ignore
