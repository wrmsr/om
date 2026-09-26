import pytest

from omcore import lang

from ..adapters import SyncToAsyncBlobStore
from ..dicts import DictBlobStore
from ..errors import InvalidBlobKeyError
from ..prefixes import PrefixedBlobStore
from ..types import BlobPrefix


def test_prefixed():
    d = DictBlobStore()
    d.put('other', b'')
    d.put('p/q-z', b'')
    s = PrefixedBlobStore(SyncToAsyncBlobStore(d), 'p/q/')

    async def inner():
        await s.put('a', b'1')
        await s.put('b/c', b'2')
        async with s.open_writer('d') as w:
            await w.write(b'3')
            await w.commit()
        await s.copy('a', 'e')
        assert (await s.head('a')).key == 'a'
        assert (await s.get('b/c')).info.key == 'b/c'
        assert [i.key async for i in s.list()] == ['a', 'b/c', 'd', 'e']
        assert [i.key async for i in s.list(start_after='b/c')] == ['d', 'e']
        assert [
            e.prefix if isinstance(e, BlobPrefix) else e.key
            async for e in s.list_shallow()
        ] == ['a', 'b/', 'd', 'e']
        await s.delete('e')
        await s.delete_many(['d'])

    lang.sync_await(inner())
    assert [i.key for i in d.list()] == ['other', 'p/q-z', 'p/q/a', 'p/q/b/c']


def test_bad_prefixes():
    s = SyncToAsyncBlobStore(DictBlobStore())
    with pytest.raises(ValueError):  # noqa
        PrefixedBlobStore(s, 'p')
    with pytest.raises(InvalidBlobKeyError):
        PrefixedBlobStore(s, 'p//')
    with pytest.raises(InvalidBlobKeyError):
        PrefixedBlobStore(s, '/')
