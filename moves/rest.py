from flask import Flask
from flask import request
from flask import Response

from . import configurations


import stomp


class Rest(Flask):
    def __init__(self):
        super().__init__(__name__)
        self.conn = stomp.Connection(
            [('127.0.0.1', configurations.STOMP_PORT)])
        self.conn.connect(wait=True)

        @self.route('/update', methods=['POST'])
        def login():
            body = request.data.decode('utf-8')
            self.conn.send(body=body,
                           destination=configurations.AMQ_QUEUE)
            return Response(body, mimetype='text/plain')

    def run(self):
        return super().run(port=configurations.REST_PORT)


def main():
    Rest().run()
