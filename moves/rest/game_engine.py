from __future__ import annotations

import logging
import typing
import uuid

import chess

from . import constants
from . import types
from .. import triopubsub


LOGS = logging.getLogger(__name__)


def handle(games: typing.Dict[str, types.GameUniverse],
           input_element: types.InputQueueElement
           ) -> typing.Iterator[types.OutputQueueElement]:
    LOGS.info('input_element: %s', input_element)

    if input_element.command == types.Command.NEW_GAME:
        game_id = str(uuid.uuid4())
        board = chess.Board()
        white = typing.cast(types.Player, input_element.white)
        black = input_element.black

        game_universe = types.GameUniverse(game_id=game_id,
                                           board=board,
                                           white=white,
                                           black=black)

        games[game_id] = game_universe

        yield types.OutputQueueElement(result=types.Result.GAME_CREATED,
                                       game_universe=game_universe)

        return

    if input_element.command == types.Command.END_GAME:
        raise NotImplementedError()

    if input_element.command == types.Command.MOVE:
        game_id = typing.cast(str, input_element.game_id)

        game_universe = games[game_id]
        move = typing.cast(str, input_element.move)
        LOGS.info('[game_id: %s, game_universe: %s, move: %s]',
                  game_id, game_universe, move)
        try:
            game_universe.board.push(game_universe.board.parse_uci(move))
        except (AssertionError, ValueError) as e:
            LOGS.exception('invalid move: %s', move)
            yield types.OutputQueueElement(result=types.Result.ERROR,
                                           game_universe=game_universe,
                                           error=e)
        else:
            LOGS.info('PUSHED')
            if game_universe.board.is_game_over():
                LOGS.info('GAME ENDED!')
                LOGS.info('result: %s', game_universe.board.result())
                LOGS.info('GAME ENDED!')
                yield types.OutputQueueElement(result=types.Result.END_GAME,
                                               game_universe=game_universe,
                                               move=move)
            else:
                yield types.OutputQueueElement(result=types.Result.MOVE,
                                               game_universe=game_universe,
                                               move=move)


async def game_engine(broker: triopubsub.Broker) -> None:
    '"passive" element: wait for inputs and handle them'

    # pub/sub "infrastructure"
    subscription_id = __name__

    await broker.add_subscription(constants.INPUT_TOPIC,
                                  subscription_id,
                                  True,
                                  types.InputQueueElement)

    # mutable multiverse
    games: typing.Dict[str, types.GameUniverse] = {}

    # main loop
    async for input_element in broker.subscribe(subscription_id,
                                                types.InputQueueElement):
        LOGS.info('input_element: %s', input_element)

        for output_element in handle(games, input_element):
            LOGS.info('output_element: %s', output_element)

            await broker.send(output_element, constants.OUTPUT_TOPIC)
