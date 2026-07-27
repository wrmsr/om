# ruff: noqa: PT009 PT027 UP006
# @om-lite
import typing as ta
import unittest

from ..errors import BufferTooLargeByteStreamBufferError
from ..errors import FrameTooLargeByteStreamBufferError
from ..framing import LengthFieldByteStreamFrameDecoder
from ..framing import LongestMatchDelimiterByteStreamFrameDecoder
from ..linear import LinearByteStreamBuffer
from ..scanning import ScanningByteStreamBuffer
from ..segmented import SegmentedByteStreamBuffer


def _view_bytes(v: ta.Any) -> bytes:
    if hasattr(v, 'tobytes'):
        return ta.cast(bytes, v.tobytes())
    # As a fallback, join segments.
    if hasattr(v, 'segments'):
        return b''.join(bytes(mv) for mv in v.segments())
    raise TypeError(v)


class TestLongestMatchDelimiterByteStreamFramer(unittest.TestCase):
    def test_overlapping_delims_defers_at_end(self) -> None:
        # delims overlap: '\r' is prefix of '\r\n'
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r', b'\r\n'])
        b = SegmentedByteStreamBuffer()

        b.write(b'abc\r')
        out = f.decode(b)
        self.assertEqual(out, [])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'abc\r')

        b.write(b'\nxyz\rq')
        out = f.decode(b)
        self.assertEqual([_view_bytes(v) for v in out], [b'abc', b'xyz'])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'q')

    def test_overlapping_delims_final_allows_short(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r', b'\r\n'])
        b = SegmentedByteStreamBuffer()
        b.write(b'abc\r')

        out = f.decode(b, final=True)
        self.assertEqual([_view_bytes(v) for v in out], [b'abc'])
        self.assertEqual(len(b), 0)

    def test_longest_match_at_same_position(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n', b'\r\n'])
        b = SegmentedByteStreamBuffer()
        b.write(b'a\r')
        b.write(b'\nb\n')

        out = f.decode(b)
        self.assertEqual([_view_bytes(v) for v in out], [b'a', b'b'])
        self.assertEqual(len(b), 0)

    def test_keep_ends(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n', b'\r\n'], keep_ends=True)
        b = SegmentedByteStreamBuffer()
        b.write(b'a\r')
        b.write(b'\nb\n')

        out = f.decode(b)
        self.assertEqual([_view_bytes(v) for v in out], [b'a\r\n', b'b\n'])
        self.assertEqual(len(b), 0)

    def test_max_size(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n'], max_size=3)
        b = SegmentedByteStreamBuffer()
        b.write(b'abcd')  # no delimiter, exceeds max_size
        with self.assertRaises(ValueError):
            f.decode(b)

        # But if delimiter appears within the limit, it's fine.
        b2 = SegmentedByteStreamBuffer()
        b2.write(b'abc\nxxxx')
        out = f.decode(b2)
        self.assertEqual([_view_bytes(v) for v in out], [b'abc'])
        self.assertEqual(b''.join(bytes(mv) for mv in b2.segments()), b'xxxx')

    def test_longest_match_framer_raises_subclasses(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n'], max_size=3)
        b = SegmentedByteStreamBuffer()
        b.write(b'abcd')  # no delimiter, exceeds max_size
        with self.assertRaises(BufferTooLargeByteStreamBufferError):
            f.decode(b)

        b2 = SegmentedByteStreamBuffer()
        b2.write(b'abcd\n')  # delimiter exists but frame payload is too large
        with self.assertRaises(FrameTooLargeByteStreamBufferError):
            f.decode(b2)


class TestLengthFieldFrameDecoder(unittest.TestCase):
    def test_basic_u32_be_two_frames_segmented(self) -> None:
        # Frame format: [u32_be length_of_payload][payload]
        dec = LengthFieldByteStreamFrameDecoder(
            length_field_offset=0,
            length_field_length=4,
            byteorder='big',
            length_adjustment=0,
            initial_bytes_to_strip=4,  # strip the length field
            max_frame_length=1024,
        )

        b = SegmentedByteStreamBuffer()
        # Two frames: "hi", "world"
        raw = (
            (2).to_bytes(4, 'big') + b'hi' +
            (5).to_bytes(4, 'big') + b'world'
        )

        # Feed in awkward chunks to exercise segmentation.
        for c in (raw[:3], raw[3:9], raw[9:13], raw[13:]):
            b.write(c)
            out = dec.decode(b)
            # collect progressively
            for v in out:
                if hasattr(v, 'to_bytes'):
                    data = v.to_bytes()  # noqa
                else:
                    data = v.tobytes()  # noqa
                # first decode call may return none until enough is buffered
                # so append to a list below
            # We'll decode again at end.

        # Decode remaining
        outs = dec.decode(b)  # noqa
        all_outs = []
        # The earlier loop didn't collect; do a straightforward decode from scratch:
        b2 = SegmentedByteStreamBuffer()
        for c in (raw[:3], raw[3:9], raw[9:13], raw[13:]):
            b2.write(c)
            for v in dec.decode(b2):
                all_outs.append(v.to_bytes() if hasattr(v, 'to_bytes') else v.tobytes())

        self.assertEqual(all_outs, [b'hi', b'world'])
        self.assertEqual(len(b2), 0)

    def test_u16_le_with_header_and_strip(self) -> None:
        # Frame: [type:u8][len:u16_le payload_length][payload]
        dec = LengthFieldByteStreamFrameDecoder(
            length_field_offset=1,
            length_field_length=2,
            byteorder='little',
            length_adjustment=0,
            initial_bytes_to_strip=3,  # strip type + len
            max_frame_length=64,
        )

        b = SegmentedByteStreamBuffer()
        frame = b'\x7f' + (3).to_bytes(2, 'little') + b'abc'
        b.write(frame)
        out = dec.decode(b)
        self.assertEqual(len(out), 1)
        v = out[0]
        self.assertEqual(v.to_bytes() if hasattr(v, 'to_bytes') else v.tobytes(), b'abc')
        self.assertEqual(len(b), 0)

    def test_length_adjustment_includes_trailer(self) -> None:
        # Frame: [u8 len_of_payload][payload][crc:u2]  (crc length included via adjustment)
        dec = LengthFieldByteStreamFrameDecoder(
            length_field_offset=0,
            length_field_length=1,
            byteorder='big',
            length_adjustment=2,       # include crc
            initial_bytes_to_strip=1,   # strip len byte
            max_frame_length=64,
        )

        b = SegmentedByteStreamBuffer()
        raw = bytes([3]) + b'abc' + b'ZZ'  # crc placeholder
        b.write(raw)
        out = dec.decode(b)
        self.assertEqual(len(out), 1)
        v = out[0]
        self.assertEqual(v.to_bytes() if hasattr(v, 'to_bytes') else v.tobytes(), b'abcZZ')
        self.assertEqual(len(b), 0)

    def test_incomplete_frame_returns_empty(self) -> None:
        dec = LengthFieldByteStreamFrameDecoder(
            length_field_length=4,
            initial_bytes_to_strip=4,
            max_frame_length=64,
        )
        b = SegmentedByteStreamBuffer()
        b.write((10).to_bytes(4, 'big') + b'abc')  # need 10 bytes payload; only 3 provided
        out = dec.decode(b)
        self.assertEqual(out, [])
        self.assertEqual(len(b), 7)

    def test_frame_too_large(self) -> None:
        dec = LengthFieldByteStreamFrameDecoder(
            length_field_length=4,
            initial_bytes_to_strip=4,
            max_frame_length=8,
        )
        b = SegmentedByteStreamBuffer()
        b.write((10).to_bytes(4, 'big') + b'0123456789')
        with self.assertRaises(FrameTooLargeByteStreamBufferError):
            dec.decode(b)

    def test_linear_backend(self) -> None:
        dec = LengthFieldByteStreamFrameDecoder(
            length_field_length=2,
            byteorder='big',
            initial_bytes_to_strip=2,
            max_frame_length=128,
        )
        b = LinearByteStreamBuffer()
        raw = (4).to_bytes(2, 'big') + b'data'
        b.write(raw[:1])
        self.assertEqual(dec.decode(b), [])
        b.write(raw[1:])
        out = dec.decode(b)
        self.assertEqual(len(out), 1)
        v = out[0]
        self.assertEqual(v.to_bytes() if hasattr(v, 'to_bytes') else v.tobytes(), b'data')
        self.assertEqual(len(b), 0)


class TestLongestMatchDelimiterFramerRegressions(unittest.TestCase):
    def test_frame_too_large_returns_decoded_frames_first(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n'], max_size=4)
        b = SegmentedByteStreamBuffer()
        b.write(b'ok\nTOOLONGFRAME\nrest')

        # Frames decoded before hitting the oversized one must be returned, not lost to the exception.
        out = f.decode(b)
        self.assertEqual([_view_bytes(v) for v in out], [b'ok'])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'TOOLONGFRAME\nrest')

        # With the oversized frame now first in line, the next call raises without consuming anything.
        with self.assertRaises(FrameTooLargeByteStreamBufferError):
            f.decode(b)
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'TOOLONGFRAME\nrest')

    def test_defers_on_partially_buffered_longer_delimiter(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r', b'\r\n\r\n'])
        b = SegmentedByteStreamBuffer()

        # b'\r' matched at 1, and the buffered b'\r\n' is a live prefix of b'\r\n\r\n' - must defer even though the
        # match does not end at the buffer end.
        b.write(b'x\r\n')
        self.assertEqual(f.decode(b), [])
        self.assertEqual(len(b), 3)

        b.write(b'\r\n')
        out = f.decode(b, include_delims=True)
        self.assertEqual([(_view_bytes(v), d) for v, d in out], [(b'x', b'\r\n\r\n')])
        self.assertEqual(len(b), 0)

    def test_emits_short_delimiter_when_longer_is_disproved(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r', b'\r\n\r\n'])
        b = SegmentedByteStreamBuffer()
        b.write(b'x\r\nq')  # 'q' disproves b'\r\n\r\n'
        out = f.decode(b, include_delims=True)
        self.assertEqual([(_view_bytes(v), d) for v, d in out], [(b'x', b'\r')])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'\nq')

    def test_final_flush_does_not_defer(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r', b'\r\n\r\n'])
        b = SegmentedByteStreamBuffer()
        b.write(b'x\r\n')
        out = f.decode(b, final=True, include_delims=True)
        self.assertEqual([(_view_bytes(v), d) for v, d in out], [(b'x', b'\r')])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'\n')


class TestLongestMatchDelimiterFramerBatchDecoding(unittest.TestCase):
    """The single-delimiter batch fast path must be indistinguishable from the general per-frame path."""

    def test_single_delim_matches_reference_across_chunkings(self) -> None:
        delim = b'\r\n'
        payloads = [b'', b'a', b'bb', b'', b'x' * 100, b'q', b'']
        data = b''.join(p + delim for p in payloads) + b'tail'

        buf_ctors = [
            SegmentedByteStreamBuffer,
            lambda: SegmentedByteStreamBuffer(chunk_size=16),
            lambda: ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=16)),
            lambda: ScanningByteStreamBuffer(SegmentedByteStreamBuffer()),
            LinearByteStreamBuffer,
            lambda: ScanningByteStreamBuffer(LinearByteStreamBuffer()),
        ]

        for chunk_size in (1, 2, 3, 7, 64, len(data)):
            for keep_ends in (False, True):
                for mk in buf_ctors:
                    f = LongestMatchDelimiterByteStreamFrameDecoder([delim], keep_ends=keep_ends)
                    buf = mk()
                    got: ta.List[ta.Any] = []
                    for i in range(0, len(data), chunk_size):
                        buf.write(data[i:i + chunk_size])
                        got.extend(v.tobytes() for v in f.decode(buf))

                    exp = [p + (delim if keep_ends else b'') for p in payloads]
                    self.assertEqual(got, exp, (chunk_size, keep_ends, mk))
                    self.assertEqual(b''.join(bytes(mv) for mv in buf.segments()), b'tail')

    def test_single_delim_include_delims(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n'])
        b = SegmentedByteStreamBuffer()
        b.write(b'a\n\nbb\nrest')
        out = f.decode(b, include_delims=True)
        self.assertEqual([(v.tobytes(), d) for v, d in out], [(b'a', b'\n'), (b'', b'\n'), (b'bb', b'\n')])
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'rest')

    def test_single_delim_keep_ends_max_size(self) -> None:
        # max_size bounds the frame *payload* (bytes before the delimiter), independent of keep_ends.
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\r\n'], keep_ends=True, max_size=4)
        b = SegmentedByteStreamBuffer()
        b.write(b'okay\r\nTOOLONG\r\nx')

        out = f.decode(b)
        self.assertEqual([v.tobytes() for v in out], [b'okay\r\n'])

        with self.assertRaises(FrameTooLargeByteStreamBufferError):
            f.decode(b)
        self.assertEqual(b''.join(bytes(mv) for mv in b.segments()), b'TOOLONG\r\nx')

    def test_single_delim_batch_views_are_stable(self) -> None:
        f = LongestMatchDelimiterByteStreamFrameDecoder([b'\n'])
        b = SegmentedByteStreamBuffer(chunk_size=32)
        b.write(b'aaa\nbbb\n')
        out = f.decode(b)

        # Views must stay valid after the buffer moves on.
        b.write(b'c' * 100)
        b.split_to(50)
        self.assertEqual([v.tobytes() for v in out], [b'aaa', b'bbb'])


class TestLengthFieldFrameDecoderRegressions(unittest.TestCase):
    def test_short_frame_length_raises(self) -> None:
        # A computed frame length smaller than the length field end offset would leave part of the header unconsumed
        # and permanently desync the stream.
        dec = LengthFieldByteStreamFrameDecoder(length_field_length=1, length_adjustment=-1)
        b = SegmentedByteStreamBuffer()
        b.write(b'\x00A')  # total frame length 0 < header size 1
        with self.assertRaises(ValueError):
            dec.decode(b)
        self.assertEqual(len(b), 2)  # nothing consumed

    def test_short_frame_returns_decoded_frames_first(self) -> None:
        dec = LengthFieldByteStreamFrameDecoder(length_field_length=1, length_adjustment=-1)
        b = SegmentedByteStreamBuffer()
        b.write(b'\x03ab' + b'\x00A')

        out = dec.decode(b)
        self.assertEqual([_view_bytes(v) for v in out], [b'\x03ab'])
        self.assertEqual(len(b), 2)

        with self.assertRaises(ValueError):
            dec.decode(b)
        self.assertEqual(len(b), 2)

    def test_frame_too_large_returns_decoded_frames_first(self) -> None:
        dec = LengthFieldByteStreamFrameDecoder(length_field_length=1, max_frame_length=4)
        b = SegmentedByteStreamBuffer()
        b.write(b'\x02ab' + b'\x09' + b'x' * 9)

        out = dec.decode(b)
        self.assertEqual([_view_bytes(v) for v in out], [b'\x02ab'])
        self.assertEqual(len(b), 10)

        with self.assertRaises(FrameTooLargeByteStreamBufferError):
            dec.decode(b)
        self.assertEqual(len(b), 10)
