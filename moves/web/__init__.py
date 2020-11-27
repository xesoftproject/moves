from __future__ import annotations

import logging

import hypercorn.config
import hypercorn.trio
import quart
import quart_trio
import trio

from .. import configurations
from .. import logs


LOGS = logging.getLogger(__name__)


def main() -> None:
    logs.setup_logs()

    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.REST_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    app = quart_trio.QuartTrio(__name__, static_url_path='/')

    @app.route('/')
    async def index() -> quart.Response:
        return await quart.current_app.send_static_file('index.html')

    @app.route('/js/configuration.js')
    async def web() -> quart.Response:
        body = await quart.render_template('configuration.js',
                                           rest_hostname=configurations.REST_HOSTNAME,
                                           rest_port=configurations.REST_PORT,
                                           stomp_port=configurations.STOMP_PORT,
                                           ws_port=configurations.WS_PORT,
                                           amq_hostname=configurations.AMQ_HOSTNAME,
                                           amq_username=configurations.AMQ_USERNAME,
                                           amq_passcode=configurations.AMQ_PASSCODE,
                                           amq_queue=configurations.AMQ_QUEUE)
        return quart.Response(body,
                              mimetype='application/javascript; charset=utf-8')

    trio.run(hypercorn.trio.serve, app, config)
