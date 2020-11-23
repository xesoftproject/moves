import unittest

from moves import web


class WebIT(unittest.TestCase):
    def test_main(self) -> None:
        web.main()
