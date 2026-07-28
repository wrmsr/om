import gzip
import io

import pytest

from .... import lang
from ...coro.stepped import buffer_bytes_stepped_reader_coro
from ...coro.stepped import read_into_bytes_stepped_coro
from ..gzip import GzipCompression


_MTIME = 1733266027
_LEVEL = 7
_DEC_DATA = b'foobar' * 128
_ENC_DATA = gzip.compress(_DEC_DATA, compresslevel=_LEVEL, mtime=_MTIME)


def _run_inc_decompressor(g, data, *, read_size=13):
    ir = io.BytesIO(data)
    ow = io.BytesIO()
    o = next(g)
    while True:
        if isinstance(o, int):
            o = g.send(ir.read(o))
        elif o is None:
            o = g.send(ir.read(read_size))
        elif isinstance(o, bytes):
            if not o:
                break
            ow.write(o)
            o = g.send(None)
        else:
            raise TypeError(o)
    return ow.getvalue()


##


def test_gzip_inc_compressor():
    ow = io.BytesIO()
    for b in read_into_bytes_stepped_coro(
            GzipCompression(level=_LEVEL, mtime=_MTIME).compress_incremental(),
            io.BytesIO(_DEC_DATA),
            read_size=13,
    ):
        ow.write(b)

    assert ow.getvalue() == _ENC_DATA


def test_gzip_inc_compressor_bytearray():
    cg = lang.capture_coroutine(GzipCompression(level=_LEVEL, mtime=_MTIME).compress_incremental())
    ow = io.BytesIO()
    chunks: list[lang.Bytes] = [bytearray(_DEC_DATA[:100]), bytearray(_DEC_DATA[100:]), b'']
    for chunk in chunks:
        r = cg.send(chunk)
        while not r.is_return and r.v is not None:
            ow.write(r.v)
            r = cg.send(None)

    assert ow.getvalue() == _ENC_DATA


##


def test_gzip_inc_decompressor():
    assert _run_inc_decompressor(GzipCompression().decompress_incremental(), _ENC_DATA) == _DEC_DATA


@pytest.mark.parametrize('read_size', [1, 13, 65536])
def test_gzip_inc_decompressor_multi_member(read_size):
    dec2 = b'barbaz' * 77
    enc = _ENC_DATA + gzip.compress(dec2, compresslevel=_LEVEL, mtime=_MTIME)
    assert gzip.decompress(enc) == _DEC_DATA + dec2

    assert _run_inc_decompressor(
        GzipCompression().decompress_incremental(),
        enc,
        read_size=read_size,
    ) == _DEC_DATA + dec2


def test_gzip_inc_decompressor_padded():
    # Gzip streams may be zero-padded - see http://www.gzip.org/#faq8
    assert _run_inc_decompressor(GzipCompression().decompress_incremental(), _ENC_DATA + b'\x00' * 27) == _DEC_DATA


def test_gzip_inc_decompressor_empty():
    assert _run_inc_decompressor(GzipCompression().decompress_incremental(), b'') == b''


@pytest.mark.parametrize('cut', [5, 12, len(_ENC_DATA) - 7, len(_ENC_DATA) - 1])
def test_gzip_inc_decompressor_truncated(cut):
    with pytest.raises(EOFError):
        _run_inc_decompressor(GzipCompression().decompress_incremental(), _ENC_DATA[:cut])


def test_gzip_inc_decompressor_trailing_junk_magic():
    with pytest.raises(gzip.BadGzipFile):
        _run_inc_decompressor(GzipCompression().decompress_incremental(), _ENC_DATA + b'\x1f')


def test_gzip_inc_decompressor_buffered():
    bg = buffer_bytes_stepped_reader_coro(GzipCompression().decompress_incremental())
    sz = 13
    l = []
    for c in lang.chunk(sz, _ENC_DATA):
        o = bg.send(bytes(c))
        while o is not None:
            assert isinstance(o, bytes)
            l.append(o)
            o = next(bg)

    o = bg.send(b'')
    while o is not None:
        assert isinstance(o, bytes)
        l.append(o)
        try:
            o = next(bg)
        except StopIteration:
            break

    # The coro must terminate cleanly with the empty terminator after a complete stream.
    assert l[-1] == b''
    assert b''.join(l) == _DEC_DATA
