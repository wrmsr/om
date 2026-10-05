import io

import pytest

from omcore import lang

from ..adapters import SyncToAsyncBlobStore
from ..dicts import DictBlobStore
from ..errors import BlobPreconditionFailedError
from ..readers import iter_blob_chunks
from ..readers import open_blob_reader
from .recording import RecordingBlobStore


DATA = bytes(range(256)) * 10


def test_reader():
    d = DictBlobStore()
    d.put('k', DATA)
    s = RecordingBlobStore(SyncToAsyncBlobStore(d))

    async def inner():
        r = await open_blob_reader(s, 'k', block_size=100)
        assert len(s.calls()) == 1
        assert r.info.size == len(DATA)
        assert await r.read(10) == DATA[:10]
        assert len(s.calls()) == 1
        assert await r.read(200) == DATA[10:210]
        assert r.tell() == 210
        r.seek(-5, io.SEEK_END)
        assert await r.read() == DATA[-5:]
        assert await r.read() == b''
        r.seek(len(DATA) + 10)
        assert await r.read(5) == b''
        r.seek(3)
        assert await r.read() == DATA[3:]
        with pytest.raises(ValueError):  # noqa
            r.seek(-1)

    lang.sync_await(inner())


def test_reader_empty_and_exact():
    d = DictBlobStore()
    d.put('e', b'')
    d.put('x', b'0123456789')
    s = SyncToAsyncBlobStore(d)

    async def inner():
        r = await open_blob_reader(s, 'e')
        assert r.info.size == 0
        assert await r.read() == b''
        assert [c async for c in iter_blob_chunks(s, 'x', chunk_size=5)] == [b'01234', b'56789']
        assert [c async for c in iter_blob_chunks(s, 'x', chunk_size=3)] == [b'012', b'345', b'678', b'9']
        assert [c async for c in iter_blob_chunks(s, 'e', chunk_size=3)] == []

    lang.sync_await(inner())


def test_reader_replaced_midway():
    d = DictBlobStore()
    d.put('k', DATA)
    s = SyncToAsyncBlobStore(d)

    async def inner():
        r = await open_blob_reader(s, 'k', block_size=100)
        assert await r.read(100) == DATA[:100]
        d.put('k', DATA[::-1])
        with pytest.raises(BlobPreconditionFailedError):
            await r.read(100)

    lang.sync_await(inner())


def test_reader_pinned_version():
    d = DictBlobStore()
    v = d.put('k', b'abc')
    d.put('k', b'def')
    with pytest.raises(BlobPreconditionFailedError):
        lang.sync_await(open_blob_reader(SyncToAsyncBlobStore(d), 'k', version=v))
