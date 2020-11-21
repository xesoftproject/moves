import logging
import unittest

from moves import rest


class RestIT(unittest.TestCase):
    def test_main(self):
        logging.basicConfig(level=logging.INFO)
        rest.main()


if __name__ == '__main__':
    unittest.main()
