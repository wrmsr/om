import bz2

import pytest

from ..bz2 import Bz2Compression
from .helpers import run_transform_chunked as _run


_DEC_DATA = b'foobar' * 128
_ENC_DATA = bz2.compress(_DEC_DATA)


def test_bz2_inc_compressor():
    out = _run(Bz2Compression().compress_incremental(), _DEC_DATA)
    assert out == _ENC_DATA


def test_bz2_inc_decompressor():
    t = Bz2Compression().decompress_incremental()
    assert _run(t, _ENC_DATA) == _DEC_DATA
    assert t.eof


def test_bz2_inc_decompressor_multi_stream():
    assert _run(Bz2Compression().decompress_incremental(), _ENC_DATA * 2) == _DEC_DATA * 2


def test_bz2_inc_decompressor_truncated():
    with pytest.raises(EOFError):
        _run(Bz2Compression().decompress_incremental(), _ENC_DATA[:-7])
