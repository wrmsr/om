"""
The conformance suite against real AWS S3 and Cloudflare R2, each skipped unless its secrets are configured:

  aws: blobs_test_aws_s3_bucket, blobs_test_aws_s3_region, aws_access_key_id, aws_secret_access_key
  r2:  blobs_test_r2_account_id, blobs_test_r2_bucket, blobs_test_r2_access_key_id, blobs_test_r2_secret_access_key

The race cases are the real check on whether an endpoint evaluates conditional writes atomically - R2's docs don't say
so explicitly, so don't trust it for manifest commits until they pass. Likewise AWS's copy capabilities should only be
enabled in its Config after this suite passes with them claimed.
"""
import uuid

import pytest

from omcore import dataclasses as dc
from omcore import lang
from omcore.secrets.tests.harness import HarnessSecrets
from ominfra.clouds.aws import auth as aws_auth

from ...prefixes import PrefixedBlobStore
from ...tests.conformance import BlobStoreConformance
from ...tests.runners import AsyncioScenarioRunner
from ..endpoints import S3Endpoint
from ..stores import MIN_PART_SIZE
from ..stores import R2_CONFIG
from ..stores import S3BlobStore
from .streaming import BufferingStreamingSender


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import asyncio as _pipelines_asyncio


pytestmark = pytest.mark.online


def make_live_store(harness, target, *, streaming_sender=None, **config_kwargs):
    secrets = harness[HarnessSecrets]

    def sec(k):
        return secrets.get_or_skip(k).reveal()

    if target == 'aws':
        region = sec('blobs_test_aws_s3_region')
        return S3BlobStore(
            bucket=sec('blobs_test_aws_s3_bucket'),
            endpoint=S3Endpoint(url=f'https://s3.{region}.amazonaws.com', region=region),
            credentials=aws_auth.AwsSigner.Credentials(sec('aws_access_key_id'), sec('aws_secret_access_key')),
            config=S3BlobStore.Config(part_size=MIN_PART_SIZE, **config_kwargs),
            http_client=_pipelines_asyncio.AsyncioIoPipelineAsyncHttpClient(),
            streaming_sender=streaming_sender,
        )

    if target == 'r2':
        account = sec('blobs_test_r2_account_id')
        return S3BlobStore(
            bucket=sec('blobs_test_r2_bucket'),
            endpoint=S3Endpoint(url=f'https://{account}.r2.cloudflarestorage.com', region='auto'),
            credentials=aws_auth.AwsSigner.Credentials(
                sec('blobs_test_r2_access_key_id'),
                sec('blobs_test_r2_secret_access_key'),
            ),
            config=dc.replace(R2_CONFIG, part_size=MIN_PART_SIZE, **config_kwargs),
            http_client=_pipelines_asyncio.AsyncioIoPipelineAsyncHttpClient(),
        )

    raise ValueError(target)


class TestLiveConformance(BlobStoreConformance):
    large_size = 11 * 1024 * 1024

    @pytest.fixture(params=['aws', 'r2'])
    def store(self, request, harness):
        st = make_live_store(harness, request.param)
        ps = PrefixedBlobStore(st, f'om-blobs-live-test/{uuid.uuid7().hex}/')
        yield ps

        async def cleanup():
            await ps.delete_many([i.key async for i in ps.list()])

        AsyncioScenarioRunner().run(cleanup)

    @pytest.fixture
    def runner(self):
        return AsyncioScenarioRunner()


def test_live_aws_streamed_put_stream(harness):
    """aws-chunked streamed uploads against real AWS - R2's aws-chunked support is unverified."""

    st = make_live_store(harness, 'aws', streamed_uploads=True, streaming_sender=BufferingStreamingSender())
    ps = PrefixedBlobStore(st, f'om-blobs-live-test/{uuid.uuid7().hex}/')
    data = b'L' * (11 * 1024 * 1024 + 7)

    async def src():
        for i in range(0, len(data), 1_000_000):
            yield data[i:i + 1_000_000]

    async def inner():
        try:
            await ps.put_stream('small', src_small(), length=5)
            assert (await ps.get('small')).data == b'hello'
            await ps.put_stream('big', src(), length=len(data))
            assert (await ps.get('big')).data == data
        finally:
            await ps.delete_many([i.key async for i in ps.list()])

    async def src_small():
        yield b'hello'

    AsyncioScenarioRunner().run(inner)
