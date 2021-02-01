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


LOGS = logging.getLogger(__name__)


REGISTERED_USERS = {'a': '', 'b': '', 'c': '', 'd': ''}


async def web() -> None:
    config = hypercorn.config.Config()
    config.bind = [f'0.0.0.0:{configurations.WEB_PORT}']
    if configurations.CERTFILE:
        config.certfile = configurations.CERTFILE
    if configurations.KEYFILE:
        config.keyfile = configurations.KEYFILE

    mk_app = quart_trio.QuartTrio(__name__, static_url_path='/')
    mk_app.secret_key = secrets.token_urlsafe(32)

    @mk_app.route('/')
    async def index() -> quart.Response:
        if 'logged_in' not in quart.session:
            return quart.redirect(quart.url_for('login_html'))

        return typing.cast(quart.Response,
                           await quart.current_app.send_static_file('index.html'))

    @mk_app.route('/js/configuration.js')
    async def web() -> quart.Response:
        body = await quart.render_template('configuration.js.jinja2',
                                           configurations=configurations)
        return quart.Response(body,
                              mimetype='application/javascript; charset=utf-8')

    @mk_app.route('/login', methods=['POST'])
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

    @mk_app.route('/logout', methods=['POST'])
    async def logout() -> quart.Response:
        quart.session.pop('logged_in', None)
        return quart.redirect(quart.url_for('login_html'))

    @mk_app.route('/register', methods=['POST'])
    async def register() -> quart.Response:
        form = await quart.request.form
        username = form['username']
        password = form['password']

        if username in REGISTERED_USERS:
            quart.session['ERROR'] = 'username in REGISTERED_USERS'
        else:
            REGISTERED_USERS[username] = password

        return quart.redirect(quart.url_for('login_html'))

    @mk_app.route('/login.html')
    async def login_html() -> quart.Response:
        body = await quart.render_template('login.html.jinja2',
                                           REGISTERED_USERS=REGISTERED_USERS)
        quart.session.pop('ERROR', None)
        return quart.Response(body)

    await hypercorn.trio.serve(mk_app, config)  # type: ignore


def main() -> None:
    logs.setup_logs(__name__)

    trio.run(web)
