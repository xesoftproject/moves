from flask import Flask
from flask import render_template

from . import configurations


class Web(Flask):
    def __init__(self):
        super().__init__(__name__)

        @self.route('/')
        def index():
            return render_template('index.html', port=configurations.REST_PORT)

    def run(self):
        return super().run(port=configurations.WEB_PORT)


def main():
    Web().run()
