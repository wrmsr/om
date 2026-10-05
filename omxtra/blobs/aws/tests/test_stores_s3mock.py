import datetime
import uuid

import pytest

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http

from .... import blobs
from ..stores import S3_MOCK_CONFIG
from .faults import RecordingAsyncHttpClient
from .harness import HarnessS3


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import sync as _pipelines_sync


pytestmark = pytest.mark.integration


MIB = 1024 * 1024


@pytest.fixture
def rec():
    return RecordingAsyncHttpClient(http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()))


@pytest.fixture
def store(harness, rec):
    return harness[HarnessS3].store(
        config=dc.replace(S3_MOCK_CONFIG, part_size=5 * MIB, list_page_size=2),
        http_client=rec,
    )


def _key(name):
    return f'{uuid.uuid7().hex}/{name}'


def _ops(rec):
    out = []
    for r in rec.requests():
        q = {p.partition('=')[0] for p in r.query.split('&') if p}
        if r.method == 'POST' and 'uploads' in q:
            out.append('create')
        elif r.method == 'PUT' and 'uploadId' in q:
            out.append('part')
        elif r.method == 'POST' and 'uploadId' in q:
            out.append('complete')
        elif r.method == 'DELETE' and 'uploadId' in q:
            out.append('abort')
        else:
            out.append(r.method.lower())
    return out


def test_small_writer_is_single_put(store, rec):
    k = _key('small')

    async def inner():
        async with store.open_writer(k) as w:
            await w.write(b'x' * 1000)
            await w.commit()

    lang.sync_await(inner())
    assert _ops(rec) == ['put']


def test_large_writer_is_multipart(store, rec):
    k = _key('large')
    data = bytes(range(256)) * (11 * MIB // 256)

    async def inner():
        async with store.open_writer(k) as w:
            for i in range(0, len(data), 1_000_000):
                await w.write(data[i:i + 1_000_000])
            await w.commit()
        assert (await store.get(k)).data == data

    lang.sync_await(inner())
    assert _ops(rec) == ['create', 'part', 'part', 'part', 'complete', 'get']
    sizes = [int(r.header('content-length')) for r in rec.requests() if 'partNumber' in r.query]
    assert sizes == [5 * MIB, 5 * MIB, len(data) - 10 * MIB]


def test_abort_on_exit_without_commit(store, rec):
    k = _key('aborted')

    async def inner():
        async with store.open_writer(k) as w:
            await w.write(b'y' * (6 * MIB))
        with pytest.raises(blobs.BlobNotFoundError):
            await store.head(k)

    lang.sync_await(inner())
    assert _ops(rec) == ['create', 'part', 'abort', 'head']


def test_unsatisfiable_range_falls_back_to_head(store, rec):
    k = _key('ten')

    async def inner():
        await store.put(k, b'0123456789')
        rec.clear()
        b = await store.get(k, byte_range=blobs.OffsetBlobRange(100))
        assert (b.data, b.info.size) == (b'', 10)

    lang.sync_await(inner())
    assert _ops(rec) == ['get', 'head']


def test_copy_missing_source(harness, rec):
    st = harness[HarnessS3].store(
        config=dc.replace(S3_MOCK_CONFIG, capabilities=blobs.ALL_BLOB_CAPABILITIES),
        http_client=rec,
    )

    async def inner():
        await st.put(_key('dst'), b'')
        rec.clear()
        with pytest.raises(blobs.BlobNotFoundError):
            await st.copy(_key('missing'), _key('dst2'), cond=blobs.IfMatch(blobs.BlobVersion('"x"')))

    lang.sync_await(inner())
    assert _ops(rec) == ['put', 'head']


def test_list_paging(store, rec):
    p = _key('')

    async def inner():
        for i in range(5):
            await store.put(f'{p}k{i}', b'')
        rec.clear()
        assert [i.key async for i in store.list(prefix=p, start_after=f'{p}k0')] == [f'{p}k{i}' for i in range(1, 5)]

    lang.sync_await(inner())
    reqs = rec.requests()
    assert len(reqs) == 2
    assert 'start-after=' in reqs[0].query and 'continuation-token' not in reqs[0].query
    assert 'start-after=' not in reqs[1].query and 'continuation-token=' in reqs[1].query


def test_no_decompress_on_data_gets(store, rec):
    k = _key('nd')

    async def inner():
        await store.put(k, b'data')
        rec.clear()
        await store.get(k)
        await store.head(k)

    lang.sync_await(inner())
    get, head = rec.requests()
    assert get.header('x-test-no-decompress') == '1'
    assert head.header('x-test-no-decompress') is None


def test_abort_stale_uploads(store):
    k = _key('stale')

    async def inner():
        await store.create_multipart_upload(k)
        now = datetime.datetime.now(tz=datetime.UTC)
        assert await store.abort_stale_uploads(prefix=k, older_than=datetime.timedelta(hours=1), now=now) == 0
        later = now + datetime.timedelta(hours=2)
        assert await store.abort_stale_uploads(prefix=k, older_than=datetime.timedelta(hours=1), now=later) == 1
        assert await store.abort_stale_uploads(prefix=k, older_than=datetime.timedelta(hours=1), now=later) == 0

    lang.sync_await(inner())
