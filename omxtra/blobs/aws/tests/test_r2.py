import dataclasses
import uuid

import pytest

from omcore import lang
from omcore.http import all as http
from ominfra.clouds.aws import auth as aws_auth

from .... import blobs
from ..endpoints import S3Endpoint
from ..stores import MIN_PART_SIZE
from ..stores import R2_CONFIG
from ..stores import S3BlobStore
from .faults import RecordingAsyncHttpClient
from .harness import HarnessS3
from .test_transport import CannedAsyncHttpClient


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import sync as _pipelines_sync


def _r2_store(client):
    return S3BlobStore(
        bucket='bkt',
        endpoint=S3Endpoint(url='https://acct.r2.cloudflarestorage.com', region='auto'),
        credentials=aws_auth.AwsSigner.Credentials('ak', 'sk'),
        config=R2_CONFIG,
        http_client=client,
    )


def test_copy_uses_cf_destination_headers():
    ok: tuple = (200, {}, b'<CopyObjectResult><ETag>"c"</ETag></CopyObjectResult>')
    c = CannedAsyncHttpClient(ok, ok)
    rec = RecordingAsyncHttpClient(c)
    st = _r2_store(rec)
    lang.sync_await(st.copy('a', 'b', cond=blobs.IfAbsent()))
    lang.sync_await(st.copy('a', 'b', cond=blobs.IfMatch(blobs.BlobVersion('"v"'))))
    r1, r2 = rec.requests()
    assert r1.header('cf-copy-destination-if-none-match') == '*'
    assert r1.header('if-none-match') is None
    assert r2.header('cf-copy-destination-if-match') == '"v"'
    assert r2.header('if-match') is None
    assert r1.url == 'https://acct.r2.cloudflarestorage.com/bkt/b'
    auth = r1.header('authorization')
    assert auth is not None
    assert '/auto/s3/aws4_request' in auth
    assert 'cf-copy-destination-if-none-match' in auth


def test_r2_rejects_unverified_delete_condition():
    st = _r2_store(CannedAsyncHttpClient())
    with pytest.raises(blobs.UnsupportedBlobOperationError):
        lang.sync_await(st.delete('k', cond=blobs.IfMatch(blobs.BlobVersion('"v"'))))


@pytest.mark.integration
def test_uniform_part_sizes(harness):
    rec = RecordingAsyncHttpClient(http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()))
    # s3mock ignores copy conditions, so exercise R2's config without them.
    cfg = dataclasses.replace(R2_CONFIG, part_size=MIN_PART_SIZE, capabilities=blobs.BlobCapability.PUT_IF_ABSENT)
    st = harness[HarnessS3].store(config=cfg, http_client=rec)
    k = f'{uuid.uuid7().hex}/r2'
    data = b'q' * (2 * MIN_PART_SIZE + 12345)

    async def inner():
        async with st.open_writer(k) as w:
            for i in range(0, len(data), 999_999):
                await w.write(data[i:i + 999_999])
            await w.commit()
        assert (await st.get(k)).data == data

    lang.sync_await(inner())
    sizes = [int(r.header('content-length') or 0) for r in rec.requests() if 'partNumber' in r.query]
    assert sizes == [MIN_PART_SIZE, MIN_PART_SIZE, 12345]
