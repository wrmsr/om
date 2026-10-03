# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ..codings import BrotliIoPiplineHttpCompressorCoding
from ..codings import BrotliIoPiplineHttpDecompressorCoding
from ..codings import IoPipelineHttpCompressionCodingUnavailableError
from ..codings import IoPipelineHttpDecompressionError
from ..codings import IoPiplineHttpDecompressorCoding
from ..codings import ZlibIoPiplineHttpCompressorCoding
from ..codings import ZlibIoPiplineHttpDecompressorCoding
from ..codings import ZstdIoPiplineHttpCompressorCoding
from ..codings import ZstdIoPiplineHttpDecompressorCoding


RAW = b''.join(b'%d:' % i for i in range(6000))


def drain(
        d: IoPiplineHttpDecompressorCoding,
        data: bytes,
        max_bytes: int,
        *,
        chunk_size: ta.Optional[int] = None,
) -> bytes:
    """Feeds the data in chunks under the needs_input contract, returning all output up to eof or exhaustion."""

    out = b''
    pos = 0
    chunk_size = chunk_size or len(data) or 1
    while not d.eof():
        if not d.needs_input():
            o = d.decompress(b'', max_bytes)
        elif pos < len(data):
            o = d.decompress(data[pos:pos + chunk_size], max_bytes)
            pos += chunk_size
        else:
            break
        if o:
            assert len(o) <= max_bytes
            out += bytes(o)
    return out


class _CodingTests:
    compressor: ta.Any
    decompressor: ta.Any

    def _compress(self, data: bytes) -> bytes:
        c = self.compressor()
        return bytes(c.compress(data) or b'') + bytes(c.finish() or b'')

    def test_fresh(self):
        d = self.decompressor()
        assert d.needs_input()
        assert not d.eof()
        assert not d.unused_data()

    def test_roundtrip_under_limits(self):
        data = self._compress(RAW)
        for max_bytes in (1, 7, 1000, 1 << 20):
            for chunk_size in (1, 13, None):
                d = self.decompressor()
                assert drain(d, data, max_bytes, chunk_size=chunk_size) == RAW
                assert d.eof()
                assert d.needs_input()

    def test_flush_makes_output_available(self):
        c = self.compressor()
        data = bytes(c.compress(b'hello') or b'') + bytes(c.flush() or b'')
        d = self.decompressor()
        assert drain(d, data, 1 << 20) == b'hello'
        assert not d.eof()

        tail = bytes(c.finish() or b'')
        assert drain(d, tail, 1 << 20) == b''
        assert d.eof()

    def test_truncated(self):
        data = self._compress(RAW)
        d = self.decompressor()
        drain(d, data[:len(data) // 2], 64)
        assert not d.eof()
        assert d.needs_input()

    def test_junk_raises(self):
        d = self.decompressor()
        try:
            drain(d, b'JUNK' * 8, 64)
        except IoPipelineHttpDecompressionError:
            pass
        else:
            raise AssertionError('did not raise')


class TestZlibCodings(_CodingTests, unittest.TestCase):
    compressor = ZlibIoPiplineHttpCompressorCoding
    decompressor = ZlibIoPiplineHttpDecompressorCoding

    def test_unused_data(self):
        data = self._compress(b'a') + b'TRAILING'
        d = self.decompressor()
        assert drain(d, data, 1 << 20) == b'a'
        assert d.eof()
        assert bytes(d.unused_data() or b'') == b'TRAILING'

    def test_input_while_draining_rejected(self):
        d = self.decompressor()
        d.decompress(self._compress(RAW), 1)
        assert not d.needs_input()
        with self.assertRaises(RuntimeError):
            d.decompress(b'x', 1)


@unittest.skipUnless(BrotliIoPiplineHttpDecompressorCoding.is_available(), 'brotli not available')
class TestBrotliCodings(_CodingTests, unittest.TestCase):
    compressor = BrotliIoPiplineHttpCompressorCoding
    decompressor = BrotliIoPiplineHttpDecompressorCoding

    def test_trailing_data_raises(self):
        d = self.decompressor()
        with self.assertRaises(IoPipelineHttpDecompressionError):
            drain(d, self._compress(b'a') + b'TRAILING', 1 << 20)

    def test_limit_is_exact(self):
        # Brotli's own limit is soft - the excess must be withheld, not handed out.
        d = self.decompressor()
        out = d.decompress(self._compress(RAW), 100)
        assert len(out or b'') == 100
        assert not d.needs_input()
        assert not d.eof()
        assert bytes(out or b'') + drain(d, b'', 100) == RAW

    def test_input_while_draining_rejected(self):
        d = self.decompressor()
        d.decompress(self._compress(RAW), 1)
        assert not d.needs_input()
        with self.assertRaises(RuntimeError):
            d.decompress(b'x', 1)


@unittest.skipUnless(ZstdIoPiplineHttpDecompressorCoding.is_available(), 'compression.zstd not available')
class TestZstdCodings(_CodingTests, unittest.TestCase):
    compressor = ZstdIoPiplineHttpCompressorCoding
    decompressor = ZstdIoPiplineHttpDecompressorCoding

    def test_unused_data(self):
        second = self._compress(b'b')
        d = self.decompressor()
        assert drain(d, self._compress(b'a') + second, 1 << 20) == b'a'
        assert d.eof()
        assert bytes(d.unused_data() or b'') == second

        d2 = self.decompressor()
        assert drain(d2, second, 1 << 20) == b'b'
        assert d2.eof()

    def test_drained_to_eof_under_limit(self):
        # zstd reports needs_input False even at eof, and raises if drained past it - eof must take precedence.
        d = self.decompressor()
        data = self._compress(b'x' * 1000)
        assert drain(d, data, 1) == b'x' * 1000
        assert d.eof()
        assert d.needs_input()


class TestUnavailableCodings(unittest.TestCase):
    def test_unavailable_codings_raise_on_construction(self):
        for cls in (
                BrotliIoPiplineHttpCompressorCoding,
                BrotliIoPiplineHttpDecompressorCoding,
                ZstdIoPiplineHttpCompressorCoding,
                ZstdIoPiplineHttpDecompressorCoding,
        ):
            if cls.is_available():
                continue
            with self.assertRaises(IoPipelineHttpCompressionCodingUnavailableError):
                cls()
