import logging
import typing

import chess.engine
import trio

from . import constants
from . import types
from .. import configurations
from .. import triopubsub


LOGS = logging.getLogger(__name__)

UnionEngine = typing.Union[chess.engine.SimpleEngine, chess.engine.UciProtocol]


async def cpu_move(engine: UnionEngine,
                   game_universe: types.GameUniverse) -> typing.AsyncIterator[types.InputQueueElement]:
    try:
        if configurations.running_on_ec2():
            import trio_asyncio
            assert isinstance(engine, chess.engine.UciProtocol)
            result = await trio_asyncio.aio_as_trio(engine.play)(game_universe.board,
                                                                 chess.engine.Limit(time=5))
        else:
            assert isinstance(engine, chess.engine.SimpleEngine)
            result = await trio.to_thread.run_sync(engine.play, game_universe.board,
                                                   chess.engine.Limit(time=5))
    except chess.engine.EngineError:
        LOGS.exception('cannot play')
        return
    else:
        move = typing.cast(chess.Move, result.move)

        yield types.InputQueueElement(command=types.Command.MOVE,
                                      game_id=game_universe.game_id,
                                      move=move.uci())


async def handle(engine: UnionEngine,
                 output_element: types.OutputQueueElement) -> typing.AsyncIterator[types.InputQueueElement]:
    if output_element.result == types.Result.ERROR:
        return  # nothing to do here

    if output_element.result == types.Result.GAME_CREATED:
        game_universe = output_element.game_universe

        if game_universe.white.player_type == types.PlayerType.CPU:
            async for input_element in cpu_move(engine, game_universe):
                yield input_element

    if output_element.result == types.Result.MOVE:
        game_universe = output_element.game_universe

        if ((game_universe.board.turn == chess.WHITE and
             game_universe.white.player_type == types.PlayerType.CPU) or
            (game_universe.board.turn == chess.BLACK and
             game_universe.black is not None and
             game_universe.black.player_type == types.PlayerType.CPU)):
            async for input_element in cpu_move(engine, game_universe):
                yield input_element

    if output_element.result == types.Result.END_GAME:
        return  # nothing to do here

    if output_element.result == types.Result.SUGGESTION:
        raise NotImplementedError()


async def cpu(broker: triopubsub.Broker) -> None:
    '"passive" element: wait for inputs and handle them'

    # pub/sub "infrastructure"
    subscription_id = __name__

    await broker.add_subscription(constants.OUTPUT_TOPIC,
                                  subscription_id,
                                  True,
                                  types.OutputQueueElement)

    # IA
    engine: UnionEngine
    try:
        if configurations.running_on_ec2():
            import trio_asyncio
            _, engine = await trio_asyncio.aio_as_trio(chess.engine.popen_uci)(configurations.STOCKFISH)
        else:
            engine = chess.engine.SimpleEngine.popen_uci(
                configurations.STOCKFISH)
    except:
        LOGS.error('configurations.STOCKFISH: %s', configurations.STOCKFISH)
        raise

    # main loop
    async for output_element in broker.subscribe(subscription_id,
                                                 types.OutputQueueElement):
        LOGS.info('output_element: %s', output_element)

        async for input_element in handle(engine, output_element):
            LOGS.info('input_element: %s', input_element)

            await broker.send(input_element, constants.INPUT_TOPIC)
