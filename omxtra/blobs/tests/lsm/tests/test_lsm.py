import datetime
import itertools
import re
import threading

import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ....adapters import SyncToAsyncBlobStore
from ....caps import BlobCapability
from ....dicts import DictBlobStore
from ....errors import BlobNotFoundError
from ....errors import UnsupportedBlobOperationError
from ....local.stores import LocalBlobStore
from ....manifests import ManifestStore
from ...faults import BlobFault
from ...faults import FaultInjectingBlobStore
from ...runners import AsyncioScenarioRunner
from ...runners import SyncAwaitScenarioRunner
from ..dbs import LsmDb
from ..dbs import manifest_prefix
from ..dbs import sst_prefix
from ..errors import LsmBrokenError
from ..errors import LsmFencedError
from ..errors import LsmSnapshotExpiredError
from ..gc import collect_garbage
from ..manifests import decode_manifest
from ..manifests import encode_manifest
from ..readers import LsmReader
from ..scenarios import SMALL_OPTIONS
from ..scenarios import collect
from ..scenarios import run_model_scenario


MANIFEST_KEY = re.compile(r'db/manifest/\d+')


@pytest.fixture(params=['dict', 'local'])
def store(request, tmp_path):
    if request.param == 'dict':
        return SyncToAsyncBlobStore(DictBlobStore())
    return SyncToAsyncBlobStore(LocalBlobStore(str(tmp_path), config=LocalBlobStore.Config(no_fsync=True)))


async def _sst_keys(s):
    return {i.key async for i in s.list(prefix=sst_prefix('db'))}


def _later(hours):
    return datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(hours=hours)


@pytest.mark.parametrize('seed', [1, 2, 3, 4])
def test_model(store, seed):
    stats = lang.sync_await(run_model_scenario(store, seed=seed, ops=300))
    assert stats.flushes + stats.compactions + stats.reopens > 0


@pytest.mark.slow
@pytest.mark.parametrize('seed', range(10, 20))
def test_model_slow(store, seed):
    lang.sync_await(run_model_scenario(store, seed=seed, ops=3000, num_keys=200))


def test_fencing(store):
    async def inner():
        a = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        await a.put(b'a', b'1')
        await a.flush()

        b = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        await a.put(b'x', b'2')
        with pytest.raises(LsmFencedError):
            await a.flush()
        with pytest.raises(LsmFencedError):
            await a.get(b'a')

        assert await b.get(b'a') == b'1'
        assert await b.get(b'x') is None

        orphans = await _sst_keys(store) - {r.key for r in b.manifest.all_ssts()}
        assert len(orphans) == 1
        await collect_garbage(store, 'db', keep_manifests=10, sst_grace=datetime.timedelta(hours=1), now=_later(0))
        assert await _sst_keys(store) >= orphans
        st = await collect_garbage(store, 'db', keep_manifests=10, sst_grace=datetime.timedelta(hours=1), now=_later(2))
        assert st.ssts_deleted == 1
        assert not (await _sst_keys(store) & orphans)
        assert await b.get(b'a') == b'1'

    lang.sync_await(inner())


@pytest.mark.parametrize('landed', ['ours', 'nothing'])
def test_indeterminate_commit_resolves(store, landed):
    async def inner():
        fs = FaultInjectingBlobStore(store)
        db = await LsmDb.open(fs, 'db', options=SMALL_OPTIONS)
        await db.put(b'a', b'1')
        fs.add_fault(BlobFault(op='put', key=MANIFEST_KEY, after=landed == 'ours'))
        await db.flush()
        assert not fs.pending_faults()
        await db.put(b'b', b'2')
        await db.close()

        db2 = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        assert await collect(db2.scan()) == [(b'a', b'1'), (b'b', b'2')]

    lang.sync_await(inner())


def test_indeterminate_commit_lost_to_rival(store):
    async def inner():
        fs = FaultInjectingBlobStore(store)
        db = await LsmDb.open(fs, 'db', options=SMALL_OPTIONS)
        await db.put(b'a', b'1')
        await db.flush()

        async def rival(s):
            ms = ManifestStore(s, prefix=manifest_prefix('db'))
            latest = check.not_none(await ms.find_latest())
            cur = decode_manifest(await ms.read(latest))
            await ms.commit(latest + 1, encode_manifest(dc.replace(cur, writer_id='rival', epoch=cur.epoch + 1)))

        await db.put(b'b', b'2')
        fs.add_fault(BlobFault(op='put', key=MANIFEST_KEY, side_effect=rival))
        with pytest.raises(LsmFencedError):
            await db.flush()

        db2 = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        assert await collect(db2.scan()) == [(b'a', b'1')]

    lang.sync_await(inner())


@pytest.mark.parametrize('landed', [True, False])
def test_unresolvable_commit_breaks(store, landed):
    async def inner():
        fs = FaultInjectingBlobStore(store)
        db = await LsmDb.open(fs, 'db', options=SMALL_OPTIONS)
        await db.put(b'a', b'1')
        for i in range(8):
            fs.add_fault(BlobFault(op='put', key=MANIFEST_KEY, after=landed and i == 0))
        with pytest.raises(LsmBrokenError):
            await db.flush()
        with pytest.raises(LsmBrokenError):
            await db.put(b'b', b'2')

        db2 = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        assert await collect(db2.scan()) == ([(b'a', b'1')] if landed else [])

    lang.sync_await(inner())


def test_crash_between_upload_and_commit(store):
    async def inner():
        fs = FaultInjectingBlobStore(store)
        db = await LsmDb.open(fs, 'db', options=SMALL_OPTIONS)
        await db.put(b'a', b'1')
        await db.flush()
        await db.put(b'b', b'2')
        fs.add_fault(BlobFault(op='put', key=MANIFEST_KEY, error=lambda k: ConnectionAbortedError(k)))
        with pytest.raises(ConnectionAbortedError):
            await db.flush()
        del db

        db2 = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        assert await collect(db2.scan()) == [(b'a', b'1')]
        orphans = await _sst_keys(store) - {r.key for r in db2.manifest.all_ssts()}
        assert len(orphans) == 1
        grace = datetime.timedelta(minutes=10)
        await collect_garbage(store, 'db', keep_manifests=1, sst_grace=grace, now=_later(0))
        assert await _sst_keys(store) >= orphans
        await collect_garbage(store, 'db', keep_manifests=1, sst_grace=grace, now=_later(1))
        assert not (await _sst_keys(store) & orphans)
        assert await collect(db2.scan()) == [(b'a', b'1')]

    lang.sync_await(inner())


def test_snapshot_isolation_and_expiry(store):
    async def inner():
        db = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        await db.put(b'a', b'1')
        await db.flush()
        r = await LsmReader.open(store, 'db', options=SMALL_OPTIONS)
        r2 = await LsmReader.open(store, 'db', options=SMALL_OPTIONS)
        assert await r.get(b'a') == b'1'

        await db.put(b'a', b'2')
        await db.put(b'b', b'3')
        await db.flush()
        await db.compact()
        assert await r.get(b'a') == b'1'
        assert await collect(r.scan()) == [(b'a', b'1')]

        await collect_garbage(store, 'db', keep_manifests=1, sst_grace=datetime.timedelta(0), now=_later(1))
        with pytest.raises(LsmSnapshotExpiredError):
            await r2.get(b'a')
        await r2.refresh()
        assert await collect(r2.scan()) == [(b'a', b'2'), (b'b', b'3')]
        with pytest.raises(BlobNotFoundError):
            await LsmReader.open(store, 'db', manifest_id=r.manifest_id, options=SMALL_OPTIONS)

    lang.sync_await(inner())


def test_requires_put_if_absent():
    s = SyncToAsyncBlobStore(DictBlobStore(capabilities=BlobCapability(0)))
    with pytest.raises(UnsupportedBlobOperationError):
        lang.sync_await(LsmDb.open(s, 'db'))


def test_auto_flush_and_compact(store):
    async def inner():
        db = await LsmDb.open(store, 'db', options=SMALL_OPTIONS)
        for i in range(400):
            await db.put(f'k{i % 97:03d}'.encode(), bytes([i % 256]) * 20)
        assert db.manifest.l1
        assert len(db.manifest.l0) < SMALL_OPTIONS.l0_compaction_trigger
        assert len(db.manifest.l1) > 1
        l1 = db.manifest.l1
        assert all(a.max_key < b.min_key for a, b in itertools.pairwise(l1))
        await db.close()

    lang.sync_await(inner())


@pytest.mark.parametrize('runner_cls', [SyncAwaitScenarioRunner, AsyncioScenarioRunner])
def test_concurrent_readers(store, runner_cls):
    runner = runner_cls()
    opts = dc.replace(SMALL_OPTIONS, memtable_max_bytes=1 << 30, l0_compaction_trigger=1 << 30)
    states: dict[int, dict[bytes, bytes]] = {}
    done = threading.Event()

    async def writer():
        try:
            db = await LsmDb.open(store, 'db', options=opts)
            states[db.manifest_id] = {}
            model: dict[bytes, bytes] = {}
            for i in range(30):
                for j in range(5):
                    k = f'k{(i * 7 + j) % 40:02d}'.encode()
                    await db.put(k, f'{i}.{j}'.encode())
                    model[k] = f'{i}.{j}'.encode()
                states[db.manifest_id + 1] = dict(model)
                await db.flush()
                if i % 5 == 4:
                    states[db.manifest_id + 1] = dict(model)
                    await db.compact()
                if i % 3 == 0:
                    await collect_garbage(
                        store,
                        'db',
                        keep_manifests=4,
                        sst_grace=datetime.timedelta(hours=1),
                        now=_later(0),
                    )
        finally:
            done.set()

    async def reader():
        checks = 0
        while not done.is_set() or checks < 3:
            try:
                r = await LsmReader.open(store, 'db', options=opts)
                got = dict(await collect(r.scan()))
            except (BlobNotFoundError, LsmSnapshotExpiredError):
                continue
            assert got == states[r.manifest_id], r.manifest_id
            checks += 1
        return checks

    async def inner():
        db = await LsmDb.open(store, 'db', options=opts)
        states[db.manifest_id] = {}
        await db.close()
        results = await runner.gather([writer, reader, reader])
        for res in results:
            assert not isinstance(res, BaseException), res

    runner.run(inner)
