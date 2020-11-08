import chess
from chess import engine
from flask import Flask
from flask import Response
from flask import request
from flask_cors import CORS, cross_origin
import stomp

from . import configurations
import json
import uuid


try:
    stockfish = engine.SimpleEngine.popen_uci(configurations.STOCKFISH)
except:
    print(f'configurations.STOCKFISH: {configurations.STOCKFISH}')
    raise


def amq_queue(game_id):
    return f'{configurations.AMQ_QUEUE}-{game_id}'


class Rest(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.conn = stomp.Connection([(configurations.AMQ_HOSTNAME,
                                       configurations.STOMP_PORT)],
                                     use_ssl=True)
        self.conn.connect(configurations.AMQ_USERNAME,
                          configurations.AMQ_PASSCODE, wait=True)
        self.cors = CORS(self)
        self.config['CORS_HEADERS'] = 'Content-Type'
        self.boards = {}

        @cross_origin()
        @self.route('/start_new_game', methods=['POST'])
        def start_new_game():
            # TODO clean self.boards!
            game_id = str(uuid.uuid4())
            board = chess.Board()
            self.boards[game_id] = board

            self.conn.send(body=json.dumps({
                'move': '',
                'table': str(board)
            }), destination=amq_queue(game_id))

            return game_id

        @cross_origin()
        @self.route('/update', methods=['POST'])
        def update():
            body = request.json
            game_id = body['game_id']
            move = body['move']

            board = self.boards[game_id]

            # first of all, push the user move
            try:
                board.push(board.parse_uci(move))
            except ValueError as e:
                return Response(e, 500,  mimetype='text/plain')
            except AssertionError as e:
                return Response(e, 500, mimetype='text/plain')
            else:
                self.conn.send(body=json.dumps({
                    'move': move,
                    'table': str(board)
                }), destination=amq_queue(game_id))

            # check if is ended
            if board.is_game_over():
                self.conn.send(body=json.dumps({
                    'move': 'GAME OVER',
                    'table': str(board)
                }), destination=amq_queue(game_id))
                return Response('GAME OVER', mimetype='text/plain')

            # ask for the cpu move
            try:
                result = stockfish.play(board, engine.Limit(time=5))
            except engine.EngineError as e:
                return Response(e, 500, mimetype='text/plain')

            # push the cpu move
            try:
                board.push(result.move)
            except AssertionError as e:
                return Response(e, 500, mimetype='text/plain')
            else:
                self.conn.send(body=json.dumps({
                    'move': result.move.uci(),
                    'table': str(board)
                }), destination=amq_queue(game_id))

            # return the board after the updates
            return Response('human-cpu step done', mimetype='text/plain')

    def run(self):
        return super().run(host='0.0.0.0',
                           port=configurations.REST_PORT,
                           ssl_context='adhoc')


def main():
    Rest().run()
