import lzma

import pytest

from ..lzma import LzmaCompression
from .helpers import run_transform_chunked as _run


_DEC_DATA = b'foobar' * 128
_ENC_DATA = lzma.compress(_DEC_DATA)


def test_lzma_inc_compressor():
    out = _run(LzmaCompression().compress_incremental(), _DEC_DATA)
    assert out == _ENC_DATA


def test_lzma_inc_decompressor():
    t = LzmaCompression().decompress_incremental()
    assert _run(t, _ENC_DATA) == _DEC_DATA
    assert t.eof


def test_lzma_inc_decompressor_truncated():
    with pytest.raises(EOFError):
        _run(LzmaCompression().decompress_incremental(), _ENC_DATA[:-7])
