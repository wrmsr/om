import unittest

from lines import LineDecoder


##


class TestLines(unittest.TestCase):
    def test_split_crlf_and_unfinished_tail(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'hel'), [])
        self.assertEqual(decoder.feed(b'lo\r'), [])
        self.assertEqual(decoder.feed(b'\nlast'), [b'hello'])
        self.assertEqual(decoder.finish(), [b'last'])
        self.assertEqual(decoder.finish(), [])

    def test_preserves_all_but_one_cr(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'a\rb\r\r\n'), [b'a\rb\r'])
        self.assertEqual(decoder.feed(b'tail\r'), [])
        self.assertEqual(decoder.finish(), [b'tail\r'])

    def test_empty_lines(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'\n\n'), [b'', b''])
        self.assertEqual(decoder.finish(), [])

    def test_finish_and_feed_after_finish(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.finish(), [])
        self.assertEqual(decoder.finish(), [])
        with self.assertRaises(ValueError):
            decoder.feed(b'')
        with self.assertRaises(ValueError):
            decoder.feed(b'hello')

    def test_binary_input(self):
        decoder = LineDecoder()
        self.assertEqual(decoder.feed(b'\xff\x00\n'), [b'\xff\x00'])

    def test_all_two_chunk_boundaries(self):
        data = b'alpha\r\n\nbeta\ngamma\r'
        expected = [b'alpha', b'', b'beta', b'gamma\r']
        for split in range(len(data) + 1):
            with self.subTest(split=split):
                decoder = LineDecoder()
                actual = decoder.feed(data[:split])
                actual.extend(decoder.feed(b''))
                actual.extend(decoder.feed(data[split:]))
                actual.extend(decoder.finish())
                self.assertEqual(actual, expected)

    def test_byte_at_a_time(self):
        decoder = LineDecoder()
        actual = []
        for byte in b'a\r\nb\nc':
            actual.extend(decoder.feed(bytes([byte])))
        actual.extend(decoder.finish())
        self.assertEqual(actual, [b'a', b'b', b'c'])
