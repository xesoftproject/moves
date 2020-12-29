from __future__ import annotations

import logging
import typing

import chess.engine

from . import constants
from . import types
from .. import configurations
from .. import triopubsub


LOGS = logging.getLogger(__name__)


def cpu_move(engine: chess.engine.SimpleEngine,
             game_universe: types.GameUniverse
             ) -> typing.Iterator[types.InputQueueElement]:
    try:
        result = engine.play(game_universe.board,
                             chess.engine.Limit(time=5))
    except chess.engine.EngineError:
        LOGS.exception('cannot play')
        return
    else:
        move = typing.cast(chess.Move, result.move)

        yield types.InputQueueElement(command=types.Command.MOVE,
                                      game_id=game_universe.game_id,
                                      move=move.uci())


def handle(engine: chess.engine.SimpleEngine,
           output_element: types.OutputQueueElement
           ) -> typing.Iterator[types.InputQueueElement]:
    if output_element.result == types.Result.ERROR:
        return  # nothing to do here

    if output_element.result == types.Result.GAME_CREATED:
        game_universe = output_element.game_universe

        if game_universe.white.player_type == types.PlayerType.CPU:
            yield from cpu_move(engine, game_universe)

    if output_element.result == types.Result.MOVE:
        game_universe = output_element.game_universe

        if ((game_universe.board.turn == chess.WHITE and game_universe.white.player_type == types.PlayerType.CPU) or
                (game_universe.board.turn == chess.BLACK and game_universe.black.player_type == types.PlayerType.CPU)):
            yield from cpu_move(engine, game_universe)

    if output_element.result == types.Result.END_GAME:
        return  # nothing to do here

    if output_element.result == types.Result.SUGGESTION:
        raise NotImplementedError()


async def cpu(broker: triopubsub.Broker) -> None:
    '"passive" element: wait for inputs and handle them'

    # pub/sub "infrastructure"
    subscription = triopubsub.Subscription[types.OutputQueueElement](__name__)
    subscriber = triopubsub.Subscriber[types.OutputQueueElement]()

    await broker.add_subscription(constants.OUTPUT_TOPIC, subscription)

    # IA
    try:
        engine = chess.engine.SimpleEngine.popen_uci(configurations.STOCKFISH)
    except:
        LOGS.error('configurations.STOCKFISH: %s', configurations.STOCKFISH)
        raise

    # main loop
    async for output_element in broker.subscribe(subscriber, __name__):
        LOGS.info('output_element: %s', output_element)

        for input_element in handle(engine, output_element):
            LOGS.info('input_element: %s', input_element)

            await broker.send_message_to(input_element, constants.INPUT_TOPIC)
