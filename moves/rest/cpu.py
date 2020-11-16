from __future__ import annotations

import logging
import typing

import chess
import chess.engine
import trio

from . import types
from .. import configurations


LOGS = logging.getLogger(__name__)


def handle(engine: chess.engine.SimpleEngine,
           output_element: types.OutputQueueElement
           ) -> typing.Iterator[types.InputQueueElement]:
    LOGS.info('output_element: %s', output_element)

    if output_element.result == types.Result.ERROR:
        pass

    if output_element.result == types.Result.GAME_CREATED:
        game_universe = output_element.game_universe

        if game_universe.white.player_type == types.PlayerType.CPU:
            # do cpu move
            try:
                result = engine.play(game_universe.board,
                                     chess.engine.Limit(time=5))
            except chess.engine.EngineError:
                LOGS.exception('cannot play')
            else:
                move = typing.cast(chess.Move, result.move)

                yield types.InputQueueElement(command=types.Command.MOVE,
                                              game_id=game_universe.game_id,
                                              move=move.uci())

    if output_element.result == types.Result.MOVE:
        raise NotImplementedError()

    if output_element.result == types.Result.END_GAME:
        raise NotImplementedError()

    if output_element.result == types.Result.SUGGESTION:
        raise NotImplementedError()


async def cpu(input_send: trio.MemorySendChannel[types.InputQueueElement],
              output_receive: trio.MemoryReceiveChannel[types.OutputQueueElement]
              ) -> None:
    async with input_send, output_receive:
        LOGS.info('cpu')

        try:
            engine = chess.engine.SimpleEngine.popen_uci(
                configurations.STOCKFISH)
        except:
            LOGS.error('configurations.STOCKFISH: %s',
                       configurations.STOCKFISH)
            raise

        async for output_element in output_receive:
            LOGS.info('output_element: %s', output_element)

            try:
                input_elements = handle(engine, output_element)
            except Exception:
                LOGS.exception('cannot handle %s - %s', output_element)
            else:
                for input_element in input_elements:
                    await input_send.send(input_element)
