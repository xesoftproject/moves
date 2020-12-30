'rest types'
from dataclasses import dataclass, asdict
import json
import typing
import uuid

from .. import types


Type = typing.Literal['cpu', 'human']




@dataclass()
class StartNewGameInput:
    user_id: str
    white: Type
    black: Type

    def _players(self
                 ) -> typing.Tuple[types.Player, typing.Optional[types.Player]]:
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
                black = types.Player(str(uuid.uuid4()), types.PlayerType.CPU)
        else:
            white = types.Player(str(uuid.uuid4()), types.PlayerType.CPU)
            if self.black == 'human':
                black = types.Player(self.user_id, types.PlayerType.HUMAN)
            else:
                black = types.Player(str(uuid.uuid4()), types.PlayerType.CPU)

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


Op = typing.Literal['add', 'remove', 'update']


@dataclass()
class GamesOutput:
    op: Op
    game_id: str
    full: bool

    def json(self) -> str:
        return json.dumps(asdict(self))
