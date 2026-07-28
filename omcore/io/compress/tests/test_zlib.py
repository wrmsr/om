import zlib

from .... import lang
from ..zlib import ZlibCompression
from .helpers import run_transform_chunked as _run


_DEC_DATA = b'foobar' * 128
_ENC_DATA = zlib.compress(_DEC_DATA)


def test_zlib_inc_compressor():
    out = _run(ZlibCompression().compress_incremental(), _DEC_DATA)
    assert zlib.decompress(out) == _DEC_DATA


def test_zlib_inc_decompressor():
    t = ZlibCompression().decompress_incremental()
    assert _run(t, _ENC_DATA) == _DEC_DATA
    assert t.eof
    assert t.result == lang.just(None)
    assert t.unused_data == b''


def test_zlib_inc_decompressor_trailing_garbage():
    # Data after the end of the stream that is not a valid new stream ends the transform and lands in unused_data.
    t = ZlibCompression().decompress_incremental()
    assert _run(t, _ENC_DATA + b'not a zlib stream') == _DEC_DATA
    assert t.eof
    assert t.unused_data.endswith(b'stream')


def test_zlib_inc_decompressor_multi_stream():
    t = ZlibCompression().decompress_incremental()
    assert _run(t, _ENC_DATA + zlib.compress(b'again')) == _DEC_DATA + b'again'
