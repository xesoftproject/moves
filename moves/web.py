from flask import Flask
from flask import render_template

from . import configurations


class Web(Flask):
    def __init__(self):
        super().__init__(__name__)

        @self.route('/')
        def index():
            return render_template('index.html')

        @self.route('/favicon.ico')
        def favicon():
            return ''

        @self.route('/<path>')
        def web(path):
            return render_template(path,
                                   rest_port=configurations.REST_PORT,
                                   ws_port=configurations.WS_PORT,
                                   amq_queue=configurations.AMQ_QUEUE)

    def run(self):
        return super().run(port=configurations.WEB_PORT)


def main():
    Web().run()
