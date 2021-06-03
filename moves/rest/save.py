from json import dump
from json import load
from logging import getLogger

from async_generator import aclosing
from chess import BLACK
from chess import WHITE

from ..triopubsub import Broker
from .constants import OUTPUT_TOPIC
from .types import OutputQueueElement
from .types import PlayerType
from .types import Result

LOGS = getLogger(__name__)

DEFAULT_FN = 'games_history.js'


def store(player_id: str, *, is_victory: bool) -> None:
    won_count_delta = 1 if is_victory else -1
    played_count_delta = 1

    with open(DEFAULT_FN, 'r') as fp:
        json = load(fp)

    if player_id not in json:
        json[player_id] = {
            'won_count': 0,
            'played_count': 0
        }
    json[player_id]['won_count'] += won_count_delta
    json[player_id]['played_count'] += played_count_delta

    with open(DEFAULT_FN, 'w') as fp:
        dump(json, fp)


async def save(broker: Broker) -> None:
    '"passive" element: wait for outputs and handle them'

    async with aclosing(broker.subscribe_topic(OUTPUT_TOPIC,
                                               OutputQueueElement)) as output_elements:  # type: ignore
        # main loop
        async for output_element in output_elements:
            LOGS.info('output_element: %s', output_element)

            if output_element is None or output_element.result != Result.END_GAME:
                continue

            game_universe = output_element.game_universe
            assert game_universe.black is not None

            outcome = game_universe.board.outcome()
            assert outcome is not None

            LOGS.info('[outcome: %s]', outcome)

            if game_universe.white.player_type == PlayerType.HUMAN:
                store(game_universe.white.player_id,
                      is_victory=outcome.winner == WHITE)

            if game_universe.black.player_type == PlayerType.HUMAN:
                store(game_universe.black.player_id,
                      is_victory=outcome.winner == BLACK)
