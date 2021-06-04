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
from typing import TypedDict, Dict

LOGS = getLogger(__name__)

DEFAULT_FN = 'games_history.json'


class PlayerGamesHistory(TypedDict):
    victories: int
    defeats: int
    draws: int


GamesHistory = Dict[str, PlayerGamesHistory]


def store(player_id: str, *, is_victory: bool) -> None:
    victories_delta = 1 if is_victory else 0
    defeats_delta = 0 if is_victory else 1
    draws_delta = 0 # not supported

    try:
        with open(DEFAULT_FN, 'r') as fp:
            json: GamesHistory = load(fp)
    except FileNotFoundError:
        json = {}

    if player_id not in json:
        json[player_id] = PlayerGamesHistory(victories=0, defeats=0, draws=0)

    json[player_id]['victories'] += victories_delta
    json[player_id]['defeats'] += defeats_delta
    json[player_id]['draws'] += draws_delta

    with open(DEFAULT_FN, 'w') as fp:
        dump(json, fp)


def load_player(player_id: str) -> PlayerGamesHistory:
    json: GamesHistory
    try:
        with open(DEFAULT_FN, 'r') as fp:
            json = load(fp)
    except FileNotFoundError:
        json = {}
    return json.get(player_id, PlayerGamesHistory(victories=0, defeats=0, draws=0))


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
