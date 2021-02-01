from logging import getLogger
from typing import Iterator, Dict
from uuid import uuid4

from chess import Board

from ..triopubsub import Broker
from .constants import INPUT_TOPIC, OUTPUT_TOPIC
from .types import GameUniverse, InputQueueElement, OutputQueueElement, Command, Result


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

        try:
            move = game_universe.board.parse_uci(input_element.move)
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
                                 move=input_element.move)
        return


async def game_engine(broker: Broker) -> None:
    '"passive" element: wait for inputs and handle them'

    # pub/sub "infrastructure"
    subscription_id = __name__

    await broker.add_subscription(INPUT_TOPIC,
                                  subscription_id,
                                  True,
                                  InputQueueElement)

    try:
        # mutable multiverse
        games: Dict[str, GameUniverse] = {}

        # main loop
        async for input_element in broker.subscribe(subscription_id,
                                                    InputQueueElement):
            LOGS.info('input_element: %s', input_element)

            for output_element in handle(games, input_element):
                LOGS.info('output_element: %s', output_element)

                await broker.send(output_element, OUTPUT_TOPIC)
    finally:
        broker.remove_subscription(INPUT_TOPIC, subscription_id)
