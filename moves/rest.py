import chess
from chess import engine
from flask import Flask
from flask import Response
from flask import request
from flask_cors import CORS, cross_origin
import stomp

from . import configurations


stockfish = engine.SimpleEngine.popen_uci(configurations.STOCKFISH)


# TODO for now there is only one board, only one game, only one player

class Rest(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.conn = stomp.Connection(
            [(configurations.AMQ_HOSTNAME, configurations.STOMP_PORT)], use_ssl=True)
        self.conn.connect(configurations.AMQ_USERNAME,
                          configurations.AMQ_PASSCODE, wait=True)
        self.board = chess.Board()
        self.cors = CORS(self)
        self.config['CORS_HEADERS'] = 'Content-Type'

        @cross_origin()
        @self.route('/update', methods=['POST'])
        def update():
            body = request.data.decode('utf-8')

            try:
                self.board.push(chess.Move.from_uci(body))
            except AssertionError as e:
                self.conn.send(body=str(e),
                               destination=configurations.AMQ_QUEUE)
            else:
                if self. board.is_game_over():
                    self.conn.send(body='GAME OVER',
                                   destination=configurations.AMQ_QUEUE)
                else:
                    try:
                        result = stockfish.play(
                            self.board, engine.Limit(time=0.1))
                    except engine.EngineError as e:
                        self.conn.send(body=str(e),
                                       destination=configurations.AMQ_QUEUE)
                    else:
                        self.board.push(result.move)
                        self.conn.send(body=str(result.move),
                                       destination=configurations.AMQ_QUEUE)

            return Response(str(self.board), mimetype='text/plain')

    def run(self):
        return super().run(port=configurations.REST_PORT)


def main():
    Rest().run()
