from moves import rest
import unittest

from moves import logs


class RestIT(unittest.TestCase):
    def test_main(self):
        logs.setup_logs()
        rest.main()
