import datetime
import uuid

import pytest

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http
from ominfra.clouds.aws import auth as aws_auth

from .... import blobs
from ..stores import S3_MOCK_CONFIG
from ..streaming import aws_chunked_body
from .clients import S3_TEST_CLIENTS
from .clients import has_httpx
from .harness import HarnessS3
from .streaming import BufferingStreamingSender
from .test_transport import CannedAsyncHttpClient
from .test_transport import _store


with lang.auto_proxy_import(globals()):
    from omcore.http.clients.pipelines import sync as _pipelines_sync


async def achunks(data, size):
    for i in range(0, len(data), size):
        yield data[i:i + size]


def _chunk_signer(n, chunk_size=8192):
    signer = aws_auth.V4AwsSigner(aws_auth.AwsSigner.Credentials('a', 'b'), 'us-east-1', 's3')
    _, cs = signer.sign_streaming(
        aws_auth.AwsSigner.Request(method='PUT', url='https://b.s3.amazonaws.com/k'),
        decoded_length=n,
        chunk_size=chunk_size,
        utcnow=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC),
    )
    return cs


@pytest.mark.parametrize('n', [0, 1, 8191, 8192, 8193, 3 * 8192, 3 * 8192 + 17])
@pytest.mark.parametrize('src_chunk', [1000, 8192, 100_000])
def test_body_matches_in_memory_encoding(n, src_chunk):
    data = bytes(i % 251 for i in range(n))
    streamed = b''.join(lang.sync_async_list(aws_chunked_body(achunks(data, src_chunk), chunk_signer=_chunk_signer(n))))
    assert streamed == aws_auth.aws_chunked_encode(data, signer=_chunk_signer(n))
    assert len(streamed) == aws_auth.aws_chunked_encoded_length(n, 8192)


def test_body_length_mismatch():
    with pytest.raises(ValueError):  # noqa
        lang.sync_async_list(aws_chunked_body(achunks(b'x' * 10, 3), chunk_signer=_chunk_signer(11)))
    with pytest.raises(ValueError):  # noqa
        lang.sync_async_list(aws_chunked_body(achunks(b'x' * 12, 3), chunk_signer=_chunk_signer(11)))


def test_default_sender_not_implemented():
    st = _store(CannedAsyncHttpClient(), config=dc.replace(S3_MOCK_CONFIG, streamed_uploads=True))
    with pytest.raises(NotImplementedError):
        lang.sync_await(st.put_stream('k', achunks(b'abc', 2), length=3))


##


MIB = 1024 * 1024


@pytest.mark.integration
@pytest.mark.parametrize('s3_client', S3_TEST_CLIENTS, ids=lambda c: c.id)
@pytest.mark.parametrize('size', [0, 100_000, 11 * MIB])
def test_streamed_put_stream_s3mock(harness, s3_client, size):
    if s3_client.needs_httpx and not has_httpx():
        pytest.skip('httpx not available')
    sender = BufferingStreamingSender()
    st = harness[HarnessS3].store(
        config=dc.replace(S3_MOCK_CONFIG, streamed_uploads=True, part_size=5 * MIB),
        http_client=s3_client.make(),
        streaming_sender=sender,
    )
    k = f'{uuid.uuid7().hex}/streamed'
    data = bytes(i % 253 for i in range(size))

    first_call_sends = []

    async def inner():
        v = await st.put_stream(k, achunks(data, 300_000), length=size, cond=blobs.IfAbsent())
        first_call_sends.append(len(sender.sent))
        got = await st.get(k)
        assert got.data == data
        assert got.info.version == v
        with pytest.raises(blobs.BlobAlreadyExistsError):
            await st.put_stream(k, achunks(data, 300_000), length=size, cond=blobs.IfAbsent())

    s3_client.make_runner().run(inner)
    assert sender.sent
    for req in sender.sent:
        h = {k2.lower(): v2 for k2, v2 in dict(req.headers).items()}  # type: ignore[arg-type,misc]
        assert h['content-encoding'] == ['aws-chunked']
        assert h['x-amz-content-sha256'] == ['STREAMING-AWS4-HMAC-SHA256-PAYLOAD']
    assert first_call_sends == [3 if size > 5 * MIB else 1]  # a single PutObject, or one UploadPart per part


@pytest.mark.integration
def test_streamed_length_mismatch_publishes_nothing(harness):
    st = harness[HarnessS3].store(
        config=dc.replace(S3_MOCK_CONFIG, streamed_uploads=True, part_size=5 * MIB),
        http_client=http.SyncAsyncHttpClient(_pipelines_sync.IoPipelineHttpClient()),
        streaming_sender=BufferingStreamingSender(),
    )
    p = f'{uuid.uuid7().hex}/'

    async def inner():
        for n, declared in [(100, 101), (100, 99), (6 * MIB, 6 * MIB + 1), (6 * MIB, 6 * MIB - 1)]:
            with pytest.raises(ValueError):  # noqa
                await st.put_stream(f'{p}{n}-{declared}', achunks(b'z' * n, 65536), length=declared)
        assert [i.key async for i in st.list(prefix=p)] == []

    lang.sync_await(inner())
