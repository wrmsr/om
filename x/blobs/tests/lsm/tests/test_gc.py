import datetime

from omcore import lang

from ....adapters import SyncToAsyncBlobStore
from ....dicts import DictBlobStore
from ....manifests import ManifestStore
from ..dbs import LsmDb
from ..dbs import manifest_prefix
from ..dbs import sst_prefix
from ..gc import collect_garbage
from ..scenarios import SMALL_OPTIONS


T0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)


class _Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now


async def _sst_keys(s):
    return {i.key async for i in s.list(prefix=sst_prefix('db'))}


async def _manifest_ids(s):
    return [i async for i in ManifestStore(s, prefix=manifest_prefix('db')).iter_ids()]


def test_grace_boundary():
    clock = _Clock()
    s = SyncToAsyncBlobStore(DictBlobStore(clock=clock))

    async def inner():
        db = await LsmDb.open(s, 'db', options=SMALL_OPTIONS)
        for i in range(3):
            await db.put(f'k{i}'.encode(), b'v')
            await db.flush()
        clock.now = T0 + datetime.timedelta(minutes=5)
        await db.compact()
        live = {r.key for r in db.manifest.all_ssts()}
        dead = await _sst_keys(s) - live
        assert len(dead) == 3

        grace = datetime.timedelta(minutes=10)
        st = await collect_garbage(s, 'db', keep_manifests=1, sst_grace=grace, now=T0 + grace)
        assert st.ssts_deleted == 0
        assert st.manifests_deleted == len(await _manifest_ids(s)) + st.manifests_deleted - 1
        assert await _manifest_ids(s) == [db.manifest_id]

        just_after = T0 + grace + datetime.timedelta(milliseconds=1)
        st = await collect_garbage(s, 'db', keep_manifests=1, sst_grace=grace, now=just_after)
        assert st.ssts_deleted == 3
        assert await _sst_keys(s) == live

        st = await collect_garbage(s, 'db', keep_manifests=1, sst_grace=grace, now=T0 + datetime.timedelta(days=365))
        assert (st.ssts_deleted, st.manifests_deleted) == (0, 0)
        assert await _sst_keys(s) == live
        await db.close()

    lang.sync_await(inner())


def test_retained_manifests_protect_ssts():
    s = SyncToAsyncBlobStore(DictBlobStore())

    async def inner():
        db = await LsmDb.open(s, 'db', options=SMALL_OPTIONS)
        await db.put(b'a', b'1')
        await db.flush()
        old = {r.key for r in db.manifest.all_ssts()}
        await db.compact()
        await db.put(b'b', b'2')
        await db.flush()
        await db.compact()
        far = T0 + datetime.timedelta(days=10000)
        await collect_garbage(s, 'db', keep_manifests=100, sst_grace=datetime.timedelta(0), now=far)
        assert old <= await _sst_keys(s)
        await collect_garbage(s, 'db', keep_manifests=1, sst_grace=datetime.timedelta(0), now=far)
        assert not (old & await _sst_keys(s))
        assert len(await _manifest_ids(s)) == 1

    lang.sync_await(inner())


def test_empty():
    s = SyncToAsyncBlobStore(DictBlobStore())
    st = lang.sync_await(collect_garbage(s, 'db', keep_manifests=1, sst_grace=datetime.timedelta(0), now=T0))
    assert (st.ssts_deleted, st.manifests_deleted) == (0, 0)
