from __future__ import annotations

import logging
import typing
import uuid

import chess
import trio

from . import types
from .. import autils




LOGS = logging.getLogger(__name__)


def handle(games: typing.Dict[str, types.GameUniverse],
           input_element: types.InputQueueElement
           ) -> typing.Iterator[types.OutputQueueElement]:
    LOGS.info('input_element: %s', input_element)

    if input_element.command == types.Command.NEW_GAME:
        game_id = str(uuid.uuid4())
        board = chess.Board()
        white = typing.cast(types.Player, input_element.white)
        black = typing.cast(types.Player, input_element.black)

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
        try:
            game_universe.board.push(game_universe.board.parse_uci(move))
        except (AssertionError, ValueError) as e:
            LOGS.exception('invalid move: %s', move)
            yield types.OutputQueueElement(result=types.Result.ERROR,
                                           game_universe=game_universe,
                                           error=e)
        else:
            yield types.OutputQueueElement(result=types.Result.MOVE,
                                           game_universe=game_universe,
                                           move=move)


async def game_engine(input_receive: trio.MemoryReceiveChannel[types.InputQueueElement],
                      output_send: typing.Union[trio.MemorySendChannel[types.OutputQueueElement], autils.MemorySendChannel[types.OutputQueueElement]]
                      ) -> None:
    async with input_receive, output_send:
        LOGS.info('game_engine')

        # mutable multiverse
        games: typing.Dict[str, types.GameUniverse] = {}

        async for input_element in input_receive:
            LOGS.info('input_element: %s', input_element)

            try:
                output_elements = handle(games, input_element)
            except Exception:
                LOGS.exception('cannot handle %s - %s', input_element)
            else:
                for output_element in output_elements:
                    await output_send.send(output_element)
