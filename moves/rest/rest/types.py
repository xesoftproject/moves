'rest types'

from __future__ import annotations

from dataclasses import dataclass, asdict
from json import dumps
from typing import Optional, Tuple, Literal
from uuid import uuid4

from .. import types


Type = Literal['cpu', 'human']


@dataclass()
class StartNewGameInput:
    user_id: str
    white: Type
    black: Type

    def _players(self
                 ) -> Tuple[types.Player, Optional[types.Player]]:
        '''4 options:
        human VS human -> white is player, black is None
        human VS cpu -> white is player, black is cpu (random id)
        cpu VS human -> white is random id, black is player
        cpu VS cpu -> 2 random ids
        '''

        if self.white == 'human':
            white = types.Player(self.user_id, types.PlayerType.HUMAN)
            if self.black == 'human':
                black = None
            else:
                black = types.Player(str(uuid4()), types.PlayerType.CPU)
        else:
            white = types.Player(str(uuid4()), types.PlayerType.CPU)
            if self.black == 'human':
                black = types.Player(self.user_id, types.PlayerType.HUMAN)
            else:
                black = types.Player(str(uuid4()), types.PlayerType.CPU)

        return (white, black)

    def input_queue_element(self) -> types.InputQueueElement:
        (white, black) = self._players()
        return types.InputQueueElement(command=types.Command.NEW_GAME,
                                       white=white,
                                       black=black)


@dataclass()
class UpdateInput:
    user_id: str
    game_id: str
    move: str

    def input_queue_element(self) -> types.InputQueueElement:
        return types.InputQueueElement(command=types.Command.MOVE,
                                       game_id=self.game_id,
                                       move=self.move)


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
    winner: Optional[str]

    @classmethod
    def from_output_queue_element(cls,
                                  output_element: types.OutputQueueElement
                                  ) -> 'RegisterOutput':
        board = output_element.game_universe.board

        return RegisterOutput(output_element.move,
                              str(board),
                              board.result() if board.is_game_over() else None)

    def json(self) -> str:
        return dumps(asdict(self))
