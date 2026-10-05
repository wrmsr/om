import pytest

from omcore import lang

from ....adapters import SyncToAsyncBlobStore
from ....dicts import DictBlobStore
from ....types import IfMatch
from ...recording import RecordingBlobStore
from ..errors import LsmCorruptionError
from ..errors import LsmSnapshotExpiredError
from ..memtables import iter_records
from ..records import LsmRecord
from ..ssts import SstReader
from ..ssts import write_ssts


def _records(n, value_size=10):
    return [
        LsmRecord(f'k{i:05d}'.encode(), None if i % 7 == 3 else bytes([i % 256]) * value_size)
        for i in range(n)
    ]


def _keys():
    c = iter(range(1000))
    return lambda: f'sst/{next(c):04d}.sst'


def test_round_trip():
    d = DictBlobStore()
    s = RecordingBlobStore(SyncToAsyncBlobStore(d))
    recs = _records(500)

    async def inner():
        [ref] = await write_ssts(s, iter_records(recs), new_key=_keys(), block_size=100)
        assert ref.entries == 500
        assert (ref.min_key, ref.max_key) == (recs[0].key, recs[-1].key)
        assert ref.size == d.head(ref.key).size

        s.clear()
        r = await SstReader.open(s, ref.key, prefetch=256)
        assert r.num_blocks > 20
        assert len(s.calls('get')) == 2  # footer tail, then the index which didn't fit in it
        assert [x async for x in r.scan()] == recs
        for rec in recs[::37]:
            assert await r.get(rec.key) == rec
        assert await r.get(b'k') is None
        assert await r.get(b'k99999') is None
        assert await r.get(b'k00001x') is None
        assert [x async for x in r.scan(b'k00100', b'k00110')] == recs[100:110]
        assert [x async for x in r.scan(b'k00100x', b'k00102')] == recs[101:102]
        assert all(c.cond == IfMatch(r.info.version) for c in s.calls('get')[1:])

    lang.sync_await(inner())


def test_single_get_open():
    s = RecordingBlobStore(SyncToAsyncBlobStore(DictBlobStore()))
    recs = _records(20)

    async def inner():
        [ref] = await write_ssts(s, iter_records(recs), new_key=_keys(), block_size=64)
        s.clear()
        r = await SstReader.open(s, ref.key, prefetch=64 * 1024)
        assert [x async for x in r.scan()] == recs
        assert len(s.calls('get')) == 1  # everything was in the prefetched tail

    lang.sync_await(inner())


def test_big_values_and_split():
    s = SyncToAsyncBlobStore(DictBlobStore())
    recs = [LsmRecord(f'k{i}'.encode(), bytes([i]) * 1000) for i in range(10)]

    async def inner():
        refs = await write_ssts(s, iter_records(recs), new_key=_keys(), block_size=64, target_size=2500)
        assert len(refs) == 4
        got = []
        for ref in refs:
            got.extend([x async for x in (await SstReader.open(s, ref.key, prefetch=100)).scan()])
        assert got == recs
        assert await write_ssts(s, iter_records([]), new_key=_keys(), block_size=64) == []

    lang.sync_await(inner())


def test_corruption_detected():
    d = DictBlobStore()
    s = SyncToAsyncBlobStore(d)

    async def inner():
        [ref] = await write_ssts(s, iter_records(_records(100)), new_key=_keys(), block_size=64)
        data = bytearray(d.get(ref.key).data)
        data[10] ^= 0xff
        d.put(ref.key, bytes(data))
        r = await SstReader.open(s, ref.key)
        with pytest.raises(LsmCorruptionError):
            [x async for x in r.scan()]  # noqa

        data = bytearray(d.get(ref.key).data)
        data[-3] ^= 0xff
        d.put(ref.key, bytes(data))
        with pytest.raises(LsmCorruptionError):
            await SstReader.open(s, ref.key)

    lang.sync_await(inner())


def test_deleted_is_expired():
    d = DictBlobStore()
    s = SyncToAsyncBlobStore(d)

    async def inner():
        [ref] = await write_ssts(s, iter_records(_records(200)), new_key=_keys(), block_size=64)
        r = await SstReader.open(s, ref.key, prefetch=100)
        d.delete(ref.key)
        with pytest.raises(LsmSnapshotExpiredError):
            await r.get(b'k00000')
        with pytest.raises(LsmSnapshotExpiredError):
            await SstReader.open(s, ref.key)

    lang.sync_await(inner())


def test_unsorted_rejected():
    s = SyncToAsyncBlobStore(DictBlobStore())
    recs = [LsmRecord(b'b', b''), LsmRecord(b'a', b'')]
    with pytest.raises(ValueError):  # noqa
        lang.sync_await(write_ssts(s, iter_records(recs), new_key=_keys(), block_size=64))
