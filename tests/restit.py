from moves import rest
import unittest
import logging



class RestIT(unittest.TestCase):
    def test_main(self):
        logging.basicConfig(level=logging.INFO)
        rest.main()
