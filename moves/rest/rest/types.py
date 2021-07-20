'rest types'

from dataclasses import asdict
from dataclasses import dataclass
from json import dumps
from typing import Literal
from typing import Optional
from typing import Tuple
from typing import TypedDict
from uuid import uuid4

from chess import BLACK
from chess import WHITE

from ..types import Command
from ..types import InputQueueElement
from ..types import Move
from ..types import OutputQueueElement
from ..types import Player
from ..types import PlayerType

Type = Literal['cpu', 'human', 'invited_human']


@dataclass()
class StartNewGameInput:
    user_id: str
    white: Type
    black: Type
    invited_user_id: Optional[str]

    def _players(self) -> Tuple[Player, Optional[Player]]:
        if self.white == 'human':
            white = Player(self.user_id, PlayerType.HUMAN)
        elif self.white == 'invited_human':
            assert self.invited_user_id is not None
            white = Player(self.invited_user_id, PlayerType.HUMAN)
        else:
            white = Player(str(uuid4()), PlayerType.CPU)

        if self.black == 'human':
            black = Player(self.user_id, PlayerType.HUMAN)
        elif self.black == 'invited_human':
            assert self.invited_user_id is not None
            black = Player(self.invited_user_id, PlayerType.HUMAN)
        else:
            black = Player(str(uuid4()), PlayerType.CPU)

        return (white, black)

    def input_queue_element(self) -> InputQueueElement:
        (white, black) = self._players()
        return InputQueueElement(command=Command.NEW_GAME,
                                 white=white,
                                 black=black)


@dataclass()
class UpdateInput:
    user_id: str
    game_id: str
    move: str

    def input_queue_element(self) -> InputQueueElement:
        return InputQueueElement(command=Command.MOVE,
                                 game_id=self.game_id,
                                 move=Move(move=self.move,
                                           user_id=self.user_id))


Op = Literal['add', 'remove', 'update']


@dataclass()
class GamesOutput:
    op: Op
    game_id: str
    full: bool

    def json(self) -> str:
        return dumps(asdict(self))


@dataclass()
class RegisterOutput:
    move: Optional[str]
    table: str
    game_ended: bool
    winner: Optional[str]  # it's the player id (or None in case of draw)
    error: Optional[str]

    @classmethod
    def from_output_queue_element(
            cls, output_element: OutputQueueElement) -> 'RegisterOutput':
        board = output_element.game_universe.board
        outcome = board.outcome()
        game_ended = outcome is not None
        winner: Optional[str] = None
        if outcome is not None:
            if outcome.winner == WHITE:
                winner = output_element.game_universe.white.player_id
            elif outcome.winner == BLACK:
                assert output_element.game_universe.black is not None
                winner = output_element.game_universe.black.player_id
            else:
                winner = None

        return RegisterOutput(move=output_element.move,
                              table=str(board),
                              game_ended=game_ended,
                              winner=winner,
                              error=str(output_element.error)
                                    if output_element.error is not None
                                    else None)

    def json(self) -> str:
        return dumps(asdict(self))


class AudioInput(TypedDict):
    user_id: str
    game_id: str
    data: bytes


class KaldiResult(TypedDict):
    text: str
