from logging import INFO
from logging import getLogger
from os import rmdir, remove
from os.path import join
from unittest import TestCase

from quart_trio.app import QuartTrio

from moves.logs import LOGS_ROOT
from moves.logs import setup_logs

from ._support_for_tests import trio_test


setup_logs('delme.log', True)
LOGS = getLogger(__name__)


def mk_app() -> QuartTrio:
    app = QuartTrio(__name__)

    @app.route('/foo')
    async def foo() -> str:
        LOGS.info('info')
        return 'foo'
    return app


class TestLogs(TestCase):
    @trio_test
    async def test_logs_local(self) -> None:
        app = mk_app()
        client = app.test_client()
        with self.assertLogs(LOGS, INFO):
            await client.get('/foo')

    def tearDown(self) -> None:
        remove(join(LOGS_ROOT, 'delme.log'))
        rmdir(LOGS_ROOT)
