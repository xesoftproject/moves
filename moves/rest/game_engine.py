import logging
import queue
import typing
import uuid

import chess
import chess.engine
import trio

from .. import configurations
from . import types

LOGS = logging.getLogger(__name__)


def handle(engine: chess.engine.SimpleEngine,
           games: typing.Dict[str, types.GameUniverse],
           input_element: types.InputQueueElement
           ) -> typing.Iterator[types.OutputQueueElement]:
    LOGS.info('input_element: %s', input_element)

    if input_element.command == types.Command.NEW_GAME:
        game_id = str(uuid.uuid4())
        board = chess.Board()
        white = typing.cast(types.Player, input_element.white)
        black = typing.cast(types.Player, input_element.black)

        game = types.GameUniverse(game_id=game_id,
                                  board=board,
                                  white=white,
                                  black=black)

        games[game_id] = game

        yield types.OutputQueueElement(game_id=game_id,
                                       result=types.Result.GAME_CREATED,
                                       board=game.board)

        return

    if input_element.command == types.Command.END_GAME:
        raise NotImplementedError()
    
    if input_element.command == types.Command.MOVE:
        game_id = typing.cast(str, input_element.game_id)

        game = games[game_id]
        move = typing.cast(str, input_element.move)
        try:
            game.board.push(game.board.parse_uci(move))
        except (AssertionError, ValueError) as e:
            yield types.OutputQueueElement(game_id=game_id,
                                           result=types.Result.ERROR,
                                           board=game.board,
                                           error=e)
        else:
            yield types.OutputQueueElement(game_id=game_id,
                                           result=types.Result.MOVE,
                                           board=game.board,
                                           move=move)


async def game_engine(input_queue: queue.Queue, output_queue: queue.Queue) -> None:
    try:
        engine = chess.engine.SimpleEngine.popen_uci(configurations.STOCKFISH)
    except:
        LOGS.error('configurations.STOCKFISH: %s', configurations.STOCKFISH)
        raise

    games: typing.Dict[str, types.GameUniverse] = {}

    while True:
        await trio.sleep(0)
        while True:
            input_element: types.InputQueueElement
            try:
                input_element = input_queue.get_nowait()
            except queue.Empty:
                break
            else:
                output_elements: typing.Iterator[types.OutputQueueElement]
                try:
                    output_elements = handle(engine, games, input_element)
                except Exception as e:
                    LOGS.error('cannot handle %s - %s', input_element, e)
                else:
                    for output_element in output_elements:
                        output_queue.put_nowait(output_element)
