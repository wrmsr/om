from ....testing import pytest as ptu
from ..lz4 import Lz4Compression
from .helpers import run_transform_chunked as _run


_DEC_DATA = b'foobar' * 128


@ptu.skip.if_cant_import('lz4.frame')
def test_lz4():
    c = Lz4Compression().compress(_DEC_DATA)
    d = Lz4Compression().decompress(c)
    assert d == _DEC_DATA

    enc = _run(Lz4Compression().compress_incremental(), _DEC_DATA)
    assert Lz4Compression().decompress(enc) == _DEC_DATA

    assert _run(Lz4Compression().decompress_incremental(), c) == _DEC_DATA


@ptu.skip.if_cant_import('lz4.frame')
def test_lz4_inc_empty():
    enc = _run(Lz4Compression().compress_incremental(), b'')
    assert _run(Lz4Compression().decompress_incremental(), enc) == b''
