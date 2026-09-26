import asyncio
import datetime
import random
import uuid

import pytest

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http

from .... import blobs
from ...plans import finish_parallel_get
from ...plans import get_part
from ...plans import plan_parallel_get
from ..stores import S3_MOCK_CONFIG
from ..uploads import abort_parallel_upload
from ..uploads import begin_parallel_upload
from ..uploads import finish_parallel_upload
from ..uploads import upload_part
from .harness import HarnessS3


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import asyncio as _pipelines_asyncio
    from omcore.http.clients.pipelines import sync as _pipelines_sync


pytestmark = pytest.mark.integration


MIB = 1024 * 1024
CONFIG = dc.replace(S3_MOCK_CONFIG, part_size=5 * MIB)
DATA = bytes(i % 247 for i in range(13 * MIB + 5))


def _sync_store(harness):
    return harness[HarnessS3].store(
        config=CONFIG,
        http_client=http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()),
    )


def _key():
    return f'{uuid.uuid7().hex}/up'


@pytest.mark.parametrize('size', [0, 1000, len(DATA)])
def test_sync_random_order(harness, size):
    st = _sync_store(harness)
    k = _key()
    data = DATA[:size]

    async def inner():
        plan = await begin_parallel_upload(st, k, size=size, cond=blobs.IfAbsent())
        parts = list(plan.parts)
        random.Random(size).shuffle(parts)
        done = [await upload_part(st, plan, p, data[p.start:p.stop]) for p in parts]
        v = await finish_parallel_upload(st, plan, done)
        got = await st.get(k)
        assert (got.data, got.info.version) == (data, v)

        # And read it back with a parallel get plan, in random order.
        gp = plan_parallel_get(got.info, part_size=4 * MIB)
        gparts = list(gp.parts)
        random.Random(size + 1).shuffle(gparts)
        assert finish_parallel_get(gp, {p.index: await get_part(st, gp, p) for p in gparts}) == data

    lang.sync_await(inner())


def test_asyncio_gather(harness):
    st = harness[HarnessS3].store(config=CONFIG, http_client=_pipelines_asyncio.AsyncioIoPipelineAsyncHttpClient())
    k = _key()

    async def inner():
        plan = await begin_parallel_upload(st, k, size=len(DATA))
        done = await asyncio.gather(*[upload_part(st, plan, p, DATA[p.start:p.stop]) for p in plan.parts])
        await finish_parallel_upload(st, plan, done)
        info = await st.head(k)
        gp = plan_parallel_get(info, part_size=3 * MIB)
        blobs_ = await asyncio.gather(*[get_part(st, gp, p) for p in gp.parts])
        assert finish_parallel_get(gp, {p.index: b for p, b in zip(gp.parts, blobs_)}) == DATA

    asyncio.run(inner())


def test_missing_part_and_rival_and_abort(harness):
    st = _sync_store(harness)
    k = _key()

    async def inner():
        plan = await begin_parallel_upload(st, k, size=len(DATA), cond=blobs.IfAbsent())
        done = [await upload_part(st, plan, p, DATA[p.start:p.stop]) for p in plan.parts[:-1]]
        with pytest.raises(blobs.BlobStoreError):
            await finish_parallel_upload(st, plan, done)
        with pytest.raises(blobs.BlobStreamLengthError):
            await upload_part(st, plan, plan.parts[-1], b'short')

        done.append(await upload_part(st, plan, plan.parts[-1], DATA[plan.parts[-1].start:]))
        await st.put(k, b'rival')
        with pytest.raises(blobs.BlobAlreadyExistsError):
            await finish_parallel_upload(st, plan, done)
        assert (await st.get(k)).data == b'rival'

        plan2 = await begin_parallel_upload(st, k + '2', size=len(DATA))
        await abort_parallel_upload(st, plan2)
        far = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=1)
        assert await st.abort_stale_uploads(prefix=k + '2', older_than=datetime.timedelta(0), now=far) == 0

    lang.sync_await(inner())
