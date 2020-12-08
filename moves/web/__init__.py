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


async def web() -> None:
    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.WEB_PORT}']
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
        body = await quart.render_template('configuration.js.jinja2',
                                           configurations=configurations)
        return quart.Response(body,
                              mimetype='application/javascript; charset=utf-8')

    await hypercorn.trio.serve(app, config)


def main() -> None:
    logs.setup_logs(__name__)

    trio.run(web)
