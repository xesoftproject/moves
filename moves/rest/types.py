import dataclasses
import enum
import typing

import chess


class PlayerType(enum.Enum):
    CPU = enum.auto()
    HUMAN = enum.auto()


@dataclasses.dataclass
class Player:
    player_id: str
    player_type: PlayerType
    player_name: typing.Optional[str] = None


@dataclasses.dataclass
class GameUniverse:
    'all the infos of a single game'

    game_id: str
    board: chess.Board
    white: Player
    black: typing.Optional[Player]


class Command(enum.Enum):
    NEW_GAME = enum.auto()
    END_GAME = enum.auto()
    MOVE = enum.auto()
    ASK_SUGGESTION = enum.auto()


@dataclasses.dataclass
class Move:
    move: str
    user_id: str

@dataclasses.dataclass
class InputQueueElement:
    command: Command

    # available only if command is NEW_GAME
    white: typing.Optional[Player] = None
    black: typing.Optional[Player] = None

    # available only if command is not NEW_GAME
    game_id: typing.Optional[str] = None

    # available only if command is MOVE
    move: typing.Optional[Move] = None


class Result(enum.Enum):
    ERROR = enum.auto()
    GAME_CREATED = enum.auto()
    MOVE = enum.auto()
    END_GAME = enum.auto()
    SUGGESTION = enum.auto()


@dataclasses.dataclass
class OutputQueueElement:
    result: Result

    game_universe: GameUniverse

    # available only with result==ERROR
    error: typing.Optional[Exception] = None

    # available only with result==MOVE
    move: typing.Optional[str] = None
