import typing as ta

import pytest

from .... import check
from .... import codecs
from .... import lang
from ....testing import pytest as ptu
from ...transforms.funcs import run_stream_transform
from ...transforms.types import StreamTransform


##


def _test_compression(name: str) -> None:
    co = codecs.lookup(name).new()
    o = b'abcd1234'
    c = co.encode(o)
    u = co.decode(c)
    assert o == u


@pytest.mark.parametrize('name', [
    'bz2',
    'gzip',
    'lzma',
])
def test_compression_codec(name: str) -> None:
    _test_compression(name)


@ptu.skip.if_cant_import('lz4')
def test_compression_lz4() -> None:
    _test_compression('lz4')


@ptu.skip.if_cant_import('snappy')
def test_compression_snappy() -> None:
    _test_compression('snappy')


def test_compression_zstd() -> None:
    _test_compression('zstd')


##


def _run_incremental_codec(t: StreamTransform[bytes, lang.Bytes, ta.Any], i: bytes) -> bytes:
    # Byte-at-a-time to stress incremental behavior.
    out = b''.join(run_stream_transform(t, (bytes([b]) for b in i)))
    assert t.eof
    return out


def _test_incremental_compression(name: str) -> None:
    co = check.not_none(codecs.lookup(name).new_incremental)()
    o = b'abcd1234'
    c = _run_incremental_codec(co.encode_incremental(), o)
    u = _run_incremental_codec(co.decode_incremental(), c)
    assert o == u


@pytest.mark.parametrize('name', [
    'bz2',
    'gzip',
    'lzma',
])
def test_incremental_compression_codec(name: str) -> None:
    _test_incremental_compression(name)
