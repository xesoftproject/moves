from flask import Flask
from flask import render_template
from flask import current_app
from flask import Response

from . import configurations


class Web(Flask):
    def __init__(self):
        super().__init__(__name__,
                         static_url_path='/')

        @self.route('/')
        def index():
            return current_app.send_static_file('index.html')

        @self.route('/js/configuration.js')
        def web():
            return Response(render_template('configuration.js',
                                            rest_hostname=configurations.REST_HOSTNAME,
                                            rest_port=configurations.REST_PORT,
                                            stomp_port=configurations.STOMP_PORT,
                                            ws_port=configurations.WS_PORT,
                                            amq_hostname=configurations.AMQ_HOSTNAME,
                                            amq_username=configurations.AMQ_USERNAME,
                                            amq_passcode=configurations.AMQ_PASSCODE,
                                            amq_queue=configurations.AMQ_QUEUE),
                            mimetype='application/javascript; charset=utf-8')

    def run(self):
        return super().run(host='0.0.0.0',
                           port=configurations.WEB_PORT,
                           ssl_context='adhoc')


def main():
    Web().run()
