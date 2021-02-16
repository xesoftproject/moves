from logging import getLogger
from typing import AsyncIterator
from typing import Union
from typing import cast

from async_generator import aclosing
from chess import BLACK
from chess import WHITE
from chess import Move
from chess.engine import EngineError
from chess.engine import Limit
from chess.engine import SimpleEngine
from chess.engine import UciProtocol
from chess.engine import popen_uci
from trio.to_thread import run_sync

from ..configurations import STOCKFISH
from ..configurations import running_on_ec2
from ..triopubsub import Broker
from .constants import INPUT_TOPIC
from .constants import OUTPUT_TOPIC
from .types import Command
from .types import GameUniverse
from .types import InputQueueElement
from .types import OutputQueueElement
from .types import PlayerType
from .types import Result

LOGS = getLogger(__name__)

UnionEngine = Union[SimpleEngine, UciProtocol]


async def cpu_move(engine: UnionEngine,
                   game_universe: GameUniverse) -> AsyncIterator[InputQueueElement]:
    try:
        if running_on_ec2():
            assert isinstance(engine, UciProtocol)
            from trio_asyncio import aio_as_trio
            result = await aio_as_trio(engine.play)(game_universe.board,
                                                    Limit(time=5))
        else:
            assert isinstance(engine, SimpleEngine)
            result = await run_sync(engine.play,
                                    game_universe.board,
                                    Limit(time=5))
    except EngineError:
        LOGS.exception('cannot play')
        return
    else:
        move = cast(Move, result.move)

        yield InputQueueElement(command=Command.MOVE,
                                game_id=game_universe.game_id,
                                move=move.uci())


async def handle(engine: UnionEngine,
                 output_element: OutputQueueElement) -> AsyncIterator[InputQueueElement]:
    if output_element.result == Result.ERROR:
        return  # nothing to do here

    if output_element.result == Result.GAME_CREATED:
        game_universe = output_element.game_universe

        if game_universe.white.player_type == PlayerType.CPU:
            async for input_element in cpu_move(engine, game_universe):
                yield input_element

    if output_element.result == Result.MOVE:
        game_universe = output_element.game_universe

        if ((game_universe.board.turn == WHITE and
             game_universe.white.player_type == PlayerType.CPU) or
            (game_universe.board.turn == BLACK and
             game_universe.black is not None and
             game_universe.black.player_type == PlayerType.CPU)):
            async for input_element in cpu_move(engine, game_universe):
                yield input_element

    if output_element.result == Result.END_GAME:
        return  # nothing to do here

    if output_element.result == Result.SUGGESTION:
        raise NotImplementedError()


async def cpu(broker: Broker) -> None:
    '"passive" element: wait for inputs and handle them'

    # IA
    engine: UnionEngine
    try:
        if running_on_ec2():
            from trio_asyncio import aio_as_trio
            _, engine = await aio_as_trio(popen_uci)(STOCKFISH)
        else:
            engine = SimpleEngine.popen_uci(STOCKFISH)
    except:
        LOGS.error('STOCKFISH: %s', STOCKFISH)
        raise

    async with aclosing(broker.subscribe_topic(OUTPUT_TOPIC,
                                               OutputQueueElement)) as output_elements:  # type: ignore
        # main loop
        async for output_element in output_elements:
            LOGS.info('output_element: %s', output_element)

            async for input_element in handle(engine, output_element):
                LOGS.info('input_element: %s', input_element)

                await broker.send(input_element, INPUT_TOPIC)
