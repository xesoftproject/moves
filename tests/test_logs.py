from logging import INFO
from logging import getLogger
from unittest import TestCase

from quart_trio.app import QuartTrio

from ._support_for_tests import trio_test

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
