# ruff: noqa: PT009 PT027
# @om-lite
import unittest

from ..segmented import SegmentedByteStreamBuffer
from ..utils import ByteStreamBuffers


class TestByteStreamBuffersSplit(unittest.TestCase):
    def test_split_single_byte_sep(self) -> None:
        b = SegmentedByteStreamBuffer()
        b.write(b'a\nbb\nrest')
        out = ByteStreamBuffers.split(b, b'\n')
        self.assertEqual([v.tobytes() for v in out], [b'a\n', b'bb\n'])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'rest')

    def test_split_multi_byte_sep(self) -> None:
        # Regression: frames must be split after the *whole* separator, not just its first byte.
        b = SegmentedByteStreamBuffer()
        b.write(b'ab\r\ncd\r\nrest')
        out = ByteStreamBuffers.split(b, b'\r\n')
        self.assertEqual([v.tobytes() for v in out], [b'ab\r\n', b'cd\r\n'])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'rest')

    def test_split_multi_byte_sep_cross_segment(self) -> None:
        b = SegmentedByteStreamBuffer()
        b.write(b'ab\r')
        b.write(b'\ncd')
        out = ByteStreamBuffers.split(b, b'\r\n')
        self.assertEqual([v.tobytes() for v in out], [b'ab\r\n'])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'cd')

    def test_split_final(self) -> None:
        b = SegmentedByteStreamBuffer()
        b.write(b'ab\r\nrest')
        out = ByteStreamBuffers.split(b, b'\r\n', final=True)
        self.assertEqual([v.tobytes() for v in out], [b'ab\r\n', b'rest'])
        self.assertEqual(len(b), 0)

    def test_split_no_sep(self) -> None:
        b = SegmentedByteStreamBuffer()
        b.write(b'abc')
        self.assertEqual(ByteStreamBuffers.split(b, b'\r\n'), [])
        self.assertEqual(len(b), 3)
