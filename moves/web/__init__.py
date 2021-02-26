import logging
import secrets
import typing

import hypercorn.config
import hypercorn.trio
import quart
import quart_trio
import trio

from .. import configurations
from .. import logs

logs.setup_logs(__name__)
LOGS = logging.getLogger(__name__)
REGISTERED_USERS = {'a': '', 'b': '', 'c': '', 'd': ''}


async def web() -> None:
    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.WEB_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    app = quart_trio.QuartTrio(__name__, static_url_path='/')
    app.secret_key = secrets.token_urlsafe(32)

    @app.route('/')
    async def index() -> quart.Response:
        if 'logged_in' not in quart.session:
            return quart.redirect(quart.url_for('login_html'))

        return typing.cast(quart.Response,
                           await quart.current_app.send_static_file('index.html'))

    @app.route('/js/configuration.js')
    async def web() -> quart.Response:
        body = await quart.render_template('configuration.js.jinja2',
                                           configurations=configurations)
        return quart.Response(body,
                              mimetype='application/javascript; charset=utf-8')

    @app.route('/login', methods=['POST'])
    async def login() -> quart.Response:
        form = await quart.request.form
        username = form['username']
        password = form['password']
        if (username not in REGISTERED_USERS
                or REGISTERED_USERS[username] != password):
            quart.session['ERROR'] = 'username not in REGISTERED_USERS or REGISTERED_USERS[username] != password'
        else:
            quart.session['logged_in'] = username

        return quart.redirect(quart.url_for('index'))

    @app.route('/logout', methods=['POST'])
    async def logout() -> quart.Response:
        quart.session.pop('logged_in', None)
        return quart.redirect(quart.url_for('login_html'))

    @app.route('/register', methods=['POST'])
    async def register() -> quart.Response:
        form = await quart.request.form
        username = form['username']
        password = form['password']

        if username in REGISTERED_USERS:
            quart.session['ERROR'] = 'username in REGISTERED_USERS'
        else:
            REGISTERED_USERS[username] = password

        return quart.redirect(quart.url_for('login_html'))

    @app.route('/login.html')
    async def login_html() -> quart.Response:
        body = await quart.render_template('login.html.jinja2',
                                           REGISTERED_USERS=REGISTERED_USERS)
        quart.session.pop('ERROR', None)
        return quart.Response(body)

    @app.before_request
    async def before_request() -> None:
        app.logger.info('[request: %s on %s',
                        quart.request.method,
                        quart.request.url)
        app.logger.info(' headers: {')
        for k, v in dict(quart.request.headers).items():
            app.logger.info('     %s: %s', k, v)
        app.logger.info(' }')

        app.logger.info(' data: %s]',
                        (await quart.request.get_data()).decode('utf-8'))

    @app.teardown_request
    def teardown_request(exception: typing.Optional[BaseException]) -> None:
        app.logger.info('[exception: %s]', exception)

    await hypercorn.trio.serve(app, config)  # type: ignore


def main() -> None:
    trio.run(web)
