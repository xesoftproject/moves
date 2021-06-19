from logging import getLogger
from typing import Dict
from typing import Iterator
from uuid import uuid4

from async_generator import aclosing
from chess import BLACK
from chess import WHITE
from chess import Board

from ..triopubsub import Broker
from .constants import INPUT_TOPIC
from .constants import OUTPUT_TOPIC
from .types import Command
from .types import GameUniverse
from .types import InputQueueElement
from .types import OutputQueueElement
from .types import Result

LOGS = getLogger(__name__)


def handle(games: Dict[str, GameUniverse],
           input_element: InputQueueElement) -> Iterator[OutputQueueElement]:
    LOGS.info('input_element: %s', input_element)

    if input_element.command == Command.NEW_GAME:
        assert input_element.white is not None

        game_universe = GameUniverse(game_id=str(uuid4()),
                                     board=Board(),
                                     white=input_element.white,
                                     black=input_element.black)

        games[game_universe.game_id] = game_universe

        yield OutputQueueElement(result=Result.GAME_CREATED,
                                 game_universe=game_universe)

        return

    if input_element.command == Command.END_GAME:
        raise NotImplementedError()

    if input_element.command == Command.MOVE:
        assert input_element.game_id is not None
        assert input_element.move is not None

        game_universe = games[input_element.game_id]
        LOGS.info('[game_universe: %s]', game_universe)

        # detect if the move is from the right player
        if ((game_universe.board.turn == WHITE and
             game_universe.white.player_id != input_element.move.user_id) or
            (game_universe.board.turn == BLACK and
             (game_universe.black is None or
              game_universe.black.player_id != input_element.move.user_id))):
            yield OutputQueueElement(result=Result.ERROR,
                                     game_universe=game_universe,
                                     error=Exception('wrong turn'))
            return

        try:
            move = game_universe.board.parse_uci(input_element.move.move)
            game_universe.board.push(move)
        except (AssertionError, ValueError) as e:
            LOGS.exception('invalid move: %s', input_element.move)
            yield OutputQueueElement(result=Result.ERROR,
                                     game_universe=game_universe,
                                     error=e)
            return

        LOGS.info('PUSHED')

        if game_universe.board.is_game_over():
            LOGS.info('GAME ENDED!')
            LOGS.info('result: %s', game_universe.board.result())
            LOGS.info('GAME ENDED!')
            result = Result.END_GAME
        else:
            result = Result.MOVE

        yield OutputQueueElement(result=result,
                                 game_universe=game_universe,
                                 move=input_element.move.move)
        return


async def game_engine(broker: Broker) -> None:
    '"passive" element: wait for inputs and handle them'

    async with aclosing(broker.subscribe_topic(INPUT_TOPIC,
                                               InputQueueElement)) as input_elements:  # type: ignore
        # mutable multiverse
        games: Dict[str, GameUniverse] = {}

        # main loop
        async for input_element in input_elements:
            LOGS.info('input_element: %s', input_element)

            if input_element is None:
                break

            for output_element in handle(games, input_element):
                LOGS.info('output_element: %s', output_element)

                broker.send(output_element, OUTPUT_TOPIC)
