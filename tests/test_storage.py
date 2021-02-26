from io import SEEK_END
from io import StringIO
from textwrap import dedent
from unittest import TestCase

from moves.rest.storage import load_broker
from moves.triopubsub import Broker


def dump(io: StringIO) -> str:
    io.seek(0)
    try:
        ret = io.read()
    finally:
        io.seek(0, SEEK_END)
    return ret


class TestRest(TestCase):
    def test_load_broker(self) -> None:
        io = StringIO(dedent('''\
                                ["foo", "topic_one"]
                                ["bar", "topic_one"]
                                [123, "topic_two"]
                                '''))
        broker = load_broker(io, Broker())

        topic_one = broker.add_topic('topic_one', str)
        self.assertListEqual(['foo', 'bar'], topic_one.messages)

        topic_two = broker.add_topic('topic_two', int)
        self.assertListEqual([123], topic_two.messages)

        topic_three = broker.add_topic('topic_three', bool)
        self.assertListEqual([], topic_three.messages)

        broker.send(456, 'topic_two')
        self.assertEqual(dedent('''\
                                   ["foo", "topic_one"]
                                   ["bar", "topic_one"]
                                   [123, "topic_two"]
                                   [456, "topic_two"]
                                   '''), dump(io))

        broker.send('baz', 'topic_three')
        self.assertEqual(dedent('''\
                                   ["foo", "topic_one"]
                                   ["bar", "topic_one"]
                                   [123, "topic_two"]
                                   [456, "topic_two"]
                                   ["baz", "topic_three"]
                                   '''), dump(io))
