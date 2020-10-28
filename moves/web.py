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
                                   rest_hostname=configurations.REST_HOSTNAME,
                                   rest_port=configurations.REST_PORT,
                                   stomp_port=configurations.STOMP_PORT,
                                   ws_port=configurations.WS_PORT,
                                   amq_hostname=configurations.AMQ_HOSTNAME,
                                   amq_username=configurations.AMQ_USERNAME,
                                   amq_passcode=configurations.AMQ_PASSCODE,
                                   amq_queue=configurations.AMQ_QUEUE)

    def run(self):
        return super().run(port=configurations.WEB_PORT)


def main():
    Web().run()
