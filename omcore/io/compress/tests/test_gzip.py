import gzip

import pytest

from .... import lang
from ...transforms.funcs import run_stream_transform
from ..gzip import GzipCompression
from .helpers import run_transform_chunked as _run


_MTIME = 1733266027
_LEVEL = 7
_DEC_DATA = b'foobar' * 128
_ENC_DATA = gzip.compress(_DEC_DATA, compresslevel=_LEVEL, mtime=_MTIME)


##


def test_gzip_inc_compressor():
    out = _run(GzipCompression(level=_LEVEL, mtime=_MTIME).compress_incremental(), _DEC_DATA)
    assert out == _ENC_DATA


def test_gzip_inc_compressor_empty():
    out = _run(GzipCompression(mtime=0).compress_incremental(), b'')
    assert gzip.decompress(out) == b''


def test_gzip_inc_compressor_bytearray():
    t = GzipCompression(level=_LEVEL, mtime=_MTIME).compress_incremental()
    out = b''.join(run_stream_transform(t, [bytearray(_DEC_DATA[:100]), bytearray(_DEC_DATA[100:])]))
    assert out == _ENC_DATA


##


def test_gzip_inc_decompressor():
    t = GzipCompression().decompress_incremental()
    assert _run(t, _ENC_DATA) == _DEC_DATA
    assert t.eof
    assert t.result == lang.just(_MTIME)
    assert t.unused_data == b''


@pytest.mark.parametrize('chunk_size', [1, 13, 65536])
def test_gzip_inc_decompressor_multi_member(chunk_size):
    dec2 = b'barbaz' * 77
    enc = _ENC_DATA + gzip.compress(dec2, compresslevel=_LEVEL, mtime=_MTIME)
    assert gzip.decompress(enc) == _DEC_DATA + dec2

    assert _run(GzipCompression().decompress_incremental(), enc, chunk_size=chunk_size) == _DEC_DATA + dec2


def test_gzip_inc_decompressor_padded():
    # Gzip streams may be zero-padded - see http://www.gzip.org/#faq8
    assert _run(GzipCompression().decompress_incremental(), _ENC_DATA + b'\x00' * 27) == _DEC_DATA


def test_gzip_inc_decompressor_empty():
    assert _run(GzipCompression().decompress_incremental(), b'') == b''


@pytest.mark.parametrize('cut', [5, 12, len(_ENC_DATA) - 7, len(_ENC_DATA) - 1])
def test_gzip_inc_decompressor_truncated(cut):
    with pytest.raises(EOFError):
        _run(GzipCompression().decompress_incremental(), _ENC_DATA[:cut])


def test_gzip_inc_decompressor_trailing_junk_magic():
    with pytest.raises(gzip.BadGzipFile):
        _run(GzipCompression().decompress_incremental(), _ENC_DATA + b'\x1f')
