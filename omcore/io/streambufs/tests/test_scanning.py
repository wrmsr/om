# ruff: noqa: PT009 PT027 RUF007 UP045
# @om-lite
import typing as ta
import unittest

from ..scanning import ScanningByteStreamBuffer
from ..segmented import SegmentedByteStreamBuffer


class _SpyFindSegmentedByteStreamBuffer:
    """Test helper: wraps a SegmentedByteStreamBuffer and records find() calls."""

    def __init__(self, buf: ta.Optional[SegmentedByteStreamBuffer] = None) -> None:
        super().__init__()

        self._buf = SegmentedByteStreamBuffer() if buf is None else buf
        self.find_calls: list[tuple[bytes, int, ta.Optional[int]]] = []
        self.find_all_in_prefix_calls: list[tuple[bytes, int]] = []

    def __len__(self) -> int:
        return len(self._buf)

    def peek(self) -> memoryview:
        return self._buf.peek()

    def segments(self) -> ta.Sequence[memoryview]:
        return self._buf.segments()

    def advance(self, n: int, /) -> None:
        self._buf.advance(n)

    def split_to(self, n: int, /):
        return self._buf.split_to(n)

    def find(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        self.find_calls.append((sub, start, end))
        return self._buf.find(sub, start, end)

    def rfind(self, sub: bytes, start: int = 0, end: ta.Optional[int] = None) -> int:
        return self._buf.rfind(sub, start, end)

    def find_all_in_prefix(self, sub: bytes, start: int = 0) -> ta.Sequence[int]:
        self.find_all_in_prefix_calls.append((sub, start))
        return self._buf.find_all_in_prefix(sub, start)

    def write(self, data, /) -> None:
        self._buf.write(data)

    def reserve(self, n: int, /) -> memoryview:
        return self._buf.reserve(n)

    def commit(self, n: int, /) -> None:
        self._buf.commit(n)


class TestScanningByteStreamBuffer(unittest.TestCase):
    def test_negative_find_progress_caches_scan_start(self) -> None:
        spy = _SpyFindSegmentedByteStreamBuffer()
        fb = ScanningByteStreamBuffer(spy)

        needle = b'\r\n\r\n'

        # Trickle bytes with repeated finds (always miss).
        for _ in range(64):
            fb.write(b'a')
            self.assertEqual(fb.find(needle), -1)

        self.assertGreater(len(spy.find_calls), 0)

        # First call should start at 0.
        self.assertEqual(spy.find_calls[0][1], 0)

        # Subsequent calls should generally not restart at 0 (except small overlap backoff).
        # For a 4-byte needle, overlap backoff is at most 3 bytes.
        starts = [c[1] for c in spy.find_calls]
        self.assertTrue(any(s > 0 for s in starts[1:]))

        # Starts should be non-decreasing overall, modulo the small overlap backoff.
        # I.e. if we consider "effective progress" = start + 3, it should be monotonic.
        prog = [s + (len(needle) - 1) for s in starts]
        for a, b in zip(prog, prog[1:]):
            self.assertLessEqual(a, b)

    def test_boundary_overlap_find(self) -> None:
        spy = _SpyFindSegmentedByteStreamBuffer()
        fb = ScanningByteStreamBuffer(spy)

        needle = b'\r\n\r\n'

        # Build up data such that the delimiter arrives across segment boundaries.
        for _ in range(20):
            fb.write(b'a')
            self.assertEqual(fb.find(needle), -1)

        fb.write(b'\r')
        self.assertEqual(fb.find(needle), -1)

        fb.write(b'\n')
        self.assertEqual(fb.find(needle), -1)

        fb.write(b'\r\n')  # completes \r\n\r\n across writes
        i = fb.find(needle)
        self.assertEqual(i, 20)

        # Consume through the delimiter and ensure cache adjusts and we can find another delimiter later.
        fb.advance(i + len(needle))

        for _ in range(5):
            fb.write(b'x')
            self.assertEqual(fb.find(needle), -1)

        fb.write(needle)
        j = fb.find(needle)
        self.assertEqual(j, 5)

    def test_non_default_range_does_not_cache(self) -> None:
        spy = _SpyFindSegmentedByteStreamBuffer()
        fb = ScanningByteStreamBuffer(spy)

        fb.write(b'abcabcabc')
        self.assertEqual(fb.find(b'abc', 3, None), 3)
        self.assertEqual(fb.find(b'abc', 4, None), 6)

    def test_find_all_in_prefix_caches_negative_progress(self) -> None:
        # Chunked inner buffer so trickle writes coalesce into one contiguous prefix.
        spy = _SpyFindSegmentedByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=64))
        fb = ScanningByteStreamBuffer(spy)

        needle = b'\r\n'

        for _ in range(32):
            fb.write(b'a')
            self.assertEqual(list(fb.find_all_in_prefix(needle)), [])

        # Scan starts must advance rather than restarting from 0 each time.
        starts = [st for _, st in spy.find_all_in_prefix_calls]
        self.assertEqual(starts[0], 0)
        self.assertGreater(starts[-1], 16)
        self.assertEqual(starts, sorted(starts))

        fb.write(b'\r\nbb\r\n')
        self.assertEqual(list(fb.find_all_in_prefix(needle)), [32, 36])

        # Consumption must adjust the cache so subsequent scans stay correct.
        fb.advance(34)
        self.assertEqual(list(fb.find_all_in_prefix(needle)), [2])

    def test_find_all_in_prefix_nondefault_start_delegates(self) -> None:
        fb = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(chunk_size=64))
        fb.write(b'X.X.X')
        self.assertEqual(list(fb.find_all_in_prefix(b'X')), [0, 2, 4])
        self.assertEqual(list(fb.find_all_in_prefix(b'X', 1)), [2, 4])
