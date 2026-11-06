import unittest

from lines import LineDecoder


##


class TestVisible(unittest.TestCase):
    def test_complete_lines(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'one\ntwo\n'), [b'one', b'two'])
        self.assertEqual(decoder.finish(), [])

    def test_crlf(self):
        self.assertEqual(LineDecoder().feed(b'one\r\n'), [b'one'])

    def test_empty(self):
        self.assertEqual(LineDecoder().feed(b''), [])
