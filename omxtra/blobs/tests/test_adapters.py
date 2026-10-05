import pytest

from omcore import lang

from ..adapters import AsyncToSyncBlobStore
from ..adapters import SyncToAsyncBlobStore
from ..dicts import DictBlobStore
from ..errors import BlobAlreadyExistsError
from ..errors import BlobNotFoundError
from ..errors import BlobStreamLengthError
from ..types import BlobPrefix
from ..types import IfAbsent
from ..types import OffsetBlobRange


def test_sync_to_async():
    async def inner():
        s = SyncToAsyncBlobStore(DictBlobStore())
        v = await s.put('a/b', b'xyz', cond=IfAbsent())
        assert (await s.head('a/b')).version == v
        assert (await s.get('a/b', byte_range=OffsetBlobRange(1))).data == b'yz'
        await s.put('a/c/d', b'')
        assert [i.key async for i in s.list()] == ['a/b', 'a/c/d']
        assert [
            e.prefix if isinstance(e, BlobPrefix) else e.key
            async for e in s.list_shallow(prefix='a/')
        ] == ['a/b', 'a/c/']
        await s.copy('a/b', 'x')
        await s.delete('x')
        await s.delete_many(['a/b', 'a/c/d'])
        assert [i.key async for i in s.list()] == []

    lang.sync_await(inner())


def test_sync_to_async_writer():
    async def inner():
        s = SyncToAsyncBlobStore(DictBlobStore())

        async with s.open_writer('w') as w:
            await w.write(b'x')
        with pytest.raises(BlobNotFoundError):
            await s.head('w')

        async with s.open_writer('w', cond=IfAbsent()) as w:
            await w.write(b'a')
            await w.write(b'b')
            await w.commit()
        assert (await s.get('w')).data == b'ab'

        async def write_then_fail():
            async with s.open_writer('w2') as w:
                await w.write(b'a')
                raise RuntimeError

        with pytest.raises(RuntimeError):
            await write_then_fail()
        with pytest.raises(BlobNotFoundError):
            await s.head('w2')

        with pytest.raises(BlobAlreadyExistsError):
            async with s.open_writer('w', cond=IfAbsent()) as w:
                await w.commit()

    lang.sync_await(inner())


def test_sync_to_async_put_stream():
    async def src(*bs):
        for b in bs:
            yield b

    async def inner():
        s = SyncToAsyncBlobStore(DictBlobStore())
        await s.put_stream('a', src(b'ab', b'cd'), length=4)
        assert (await s.get('a')).data == b'abcd'
        with pytest.raises(BlobStreamLengthError):
            await s.put_stream('b', src(b'ab'), length=3)
        with pytest.raises(BlobNotFoundError):
            await s.head('b')

    lang.sync_await(inner())


def test_async_to_sync_round_trip():
    d = DictBlobStore()
    s = SyncToAsyncBlobStore(AsyncToSyncBlobStore(SyncToAsyncBlobStore(d)))

    async def inner():
        await s.put('a', b'1')
        await s.put_stream('b', _agen([b'2', b'3']), length=2)
        async with s.open_writer('c') as w:
            await w.write(b'4')
            await w.commit()
        assert [i.key async for i in s.list()] == ['a', 'b', 'c']
        assert (await s.get('b')).data == b'23'

    lang.sync_await(inner())
    assert d.get('c').data == b'4'


async def _agen(bs):
    for b in bs:
        yield b


def test_async_to_sync():
    d = DictBlobStore()
    s = AsyncToSyncBlobStore(SyncToAsyncBlobStore(d))
    s.put('a', b'1')
    s.put_stream('b', iter([b'2', b'3']), length=2)
    with pytest.raises(BlobStreamLengthError):
        s.put_stream('x', iter([b'2']), length=2)
    with s.open_writer('c') as w:
        w.write(b'4')
        w.commit()
    with s.open_writer('d') as w:
        w.write(b'5')
    assert [i.key for i in s.list()] == ['a', 'b', 'c']
    assert s.get('b').data == b'23'
    s.copy('a', 'e')
    s.delete_many(['a', 'b'])
    s.delete('c')
    assert [i.key for i in s.list()] == ['e']


def test_async_to_sync_abandoned_listing_closes():
    closed = []

    class Tracking(SyncToAsyncBlobStore):
        async def list(self, *, prefix='', start_after=None):
            try:
                async for i in super().list(prefix=prefix, start_after=start_after):
                    yield i
            finally:
                closed.append(True)

    d = DictBlobStore()
    for k in 'abc':
        d.put(k, b'')
    s = AsyncToSyncBlobStore(Tracking(d))
    it = s.list()
    assert next(it).key == 'a'
    it.close()  # type: ignore[attr-defined]
    assert closed == [True]
