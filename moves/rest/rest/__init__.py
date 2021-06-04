from base64 import b64decode
from json import dumps
from json import loads
from logging import getLogger
from typing import cast

from async_generator import aclosing
from hypercorn.config import Config
from hypercorn.trio import serve
from pkg_resources import resource_filename
from quart import request
from quart import websocket
from quart_cors import cors
from quart_trio import QuartTrio
from trio import open_nursery
from vosk import KaldiRecognizer
from vosk import Model

from moves.rest.rest.types import AudioInput
from moves.rest.rest.types import KaldiResult

from ...configurations import CERTFILE
from ...configurations import HOSTNAME
from ...configurations import KEYFILE
from ...configurations import REST_PORT
from ...triopubsub import Broker
from ..constants import INPUT_TOPIC
from ..constants import OUTPUT_TOPIC
from ..types import OutputQueueElement
from ..types import Result
from .types import GamesOutput
from .types import RegisterOutput
from .types import StartNewGameInput
from .types import UpdateInput
from ..save import load_player, PlayerGamesHistory

LETTERS = 'a', 'bi', 'ci', 'di', 'e', 'effe', 'gi', 'acca'
NUMBERS = 'uno', 'due', 'tre', 'quattro', 'cinque', 'sei', 'sette', 'otto'

LOGS = getLogger(__name__)


def clean(raw: str) -> str:
    return {'a': 'a',
            'bi': 'b',
            'ci': 'c',
            'di': 'd',
            'e': 'e',
            'effe': 'f',
            'gi': 'g',
            'acca': 'h',
            'uno': '1',
            'due': '2',
            'tre': '3',
            'quattro': '4',
            'cinque': '5',
            'sei': '6',
            'sette': '7',
            'otto': '8'}[raw]


async def mk_app(broker: Broker) -> QuartTrio:
    # pub/sub "infrastructure"
    topic_games_id = 'games'

    broker.add_topic(topic_games_id, str)

    app = cast(QuartTrio, cors(QuartTrio(__name__),
                               allow_origin=f'https://{HOSTNAME}',
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

    @app.websocket('/register/<string:game_id>')
    async def register(game_id: str) -> None:
        getLogger('VITO').info('register(%s)', game_id)

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
        LOGS.info('update [body: %s]', body)

        update_input = UpdateInput(**body)
        LOGS.info('update [update_input: %s]', update_input)

        input_element = update_input.input_queue_element()
        LOGS.info('update [input_element: %s]', input_element)

        broker.send(input_element, INPUT_TOPIC)

        return str(input_element)

    @app.websocket('/micdrop/<string:samplerate>')
    async def micdrop(samplerate: str = '44100') -> None:
        LOGS.info('micdrop(samplerate: %s)', samplerate)

        await websocket.accept()

        rec = KaldiRecognizer(Model(resource_filename('moves', 'model')),
                              int(samplerate),
                              dumps([f'{letter} {number}'
                                     for letter in LETTERS
                                     for number in NUMBERS]))

        while True:
            data = await websocket.receive()

            if rec.AcceptWaveform(data):
                await websocket.send_json(loads(rec.Result()))

    @app.websocket('/moves/<string:samplerate>')
    async def moves(samplerate: str = '44100') -> None:
        '''expecte 3 fields for each message
        user_id: str
        game_id: str
        data: bytes

        send back a json with 'error' or 'success' fields
        '''

        LOGS.info('moves(samplerate: %s)', samplerate)

        await websocket.accept()

        rec = KaldiRecognizer(Model(resource_filename('moves', 'model')),
                              int(samplerate),
                              dumps([f'{letter} {number}'
                                     for letter in LETTERS
                                     for number in NUMBERS]))

        while True:
            audio_input: AudioInput = loads(await websocket.receive())
            LOGS.info('moves [audio_input: %s]', {**audio_input, 'data': None})

            data = b64decode(audio_input['data'])

            if rec.AcceptWaveform(data):
                result: KaldiResult = loads(rec.Result())
                LOGS.info('moves [result: %s]', result)

                text = result.get('text')

                if text is None:
                    LOGS.warning('moves [text: %s]', text)
                    await websocket.send_json({'error': 'no text recognized'})
                    continue

                # text *MUST* be 4 words, letter, number, letter, number
                words = text.split()
                if (len(words) != 4
                        or words[0] not in LETTERS
                        or words[1] not in NUMBERS
                        or words[2] not in LETTERS
                        or words[3] not in NUMBERS):
                    LOGS.warning('moves [words: %s]', words)
                    await websocket.send_json({'error': 'please send "FROM" and "TO" coordinates, in the form A1B2'})
                    continue

                move = ''.join(map(clean, words))

                update_input = UpdateInput(user_id=audio_input['user_id'],
                                           game_id=audio_input['game_id'],
                                           move=move)
                LOGS.info('moves [update_input: %s]', update_input)

                input_element = update_input.input_queue_element()
                LOGS.info('moves [input_element: %s]', input_element)

                broker.send(input_element, INPUT_TOPIC)

                await websocket.send_json({'success': str(input_element)})

    @app.route('/player_games_history/<string:player_id>', methods=['GET'])
    async def player_games_history(player_id: str) -> PlayerGamesHistory:
        LOGS.info('player_games_history (player_id: %s)', player_id)
        ret = load_player(player_id)
        LOGS.info('player_games_history [ret: %s]', ret)
        return ret

    return app


async def rest(broker: Broker) -> None:
    'rest/ws server, expose the game engine to users'

    config = Config()
    config.bind = [f'0.0.0.0:{REST_PORT}']
    config.certfile = CERTFILE
    config.keyfile = KEYFILE

    await serve(await mk_app(broker), config)  # type: ignore
