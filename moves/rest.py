from flask import Flask
from flask import request

from . import configurations


class Rest(Flask):
    def __init__(self):
        super().__init__(__name__)

        @self.route('/update', methods=['POST'])
        def login():
            print(request)
            print(dir(request))
            return 'received request'

    def run(self):
        return super().run(port=configurations.REST_PORT)


def main():
    Rest().run()
