import random

import pytest

from omcore import lang
from omcore.asyncs.asynclite import all as asl
from omcore.http import all as http
from omcore.io.readers import AsyncBytesReaders
from ominfra.clouds.aws import auth as aws_auth

from .... import blobs
from ..endpoints import S3Endpoint
from ..retries import SimpleS3RetryPolicy
from ..stores import S3BlobStore


OK_PUT = (200, {'ETag': '"e"'}, b'')


def err(status, code):
    return (status, {'Content-Type': 'application/xml'}, f'<Error><Code>{code}</Code></Error>'.encode())


class CannedAsyncHttpClient(http.AsyncHttpClient):
    """Answers each request with the next canned response, or raises HttpClientError from a canned exception."""

    def __init__(self, *responses):
        super().__init__()
        self._responses = list(responses)
        self.requests = []

    async def _stream_request(self, ctx, req):
        self.requests.append(req)
        r = self._responses.pop(0)
        if isinstance(r, BaseException):
            raise http.HttpClientError from r
        status, headers, body = r
        return http.AsyncStreamHttpClientResponse(
            status=status,
            headers=http.HttpHeaders({**headers, 'Content-Length': str(len(body))}),
            request=req,
            _stream=AsyncBytesReaders.of_bytes(body),
        )


class RecordingSleeps(asl.Sleeps):
    def __init__(self):
        super().__init__()
        self.delays = []

    async def sleep(self, delay):
        self.delays.append(delay)


def _store(client, *, policy=None, **kwargs):
    return S3BlobStore(
        bucket='bkt',
        endpoint=S3Endpoint(url='http://s3.example.com', region='us-east-1'),
        credentials=aws_auth.AwsSigner.Credentials('a', 'b'),
        http_client=client,
        retry_policy=policy,
        **kwargs,
    )


def _policy(**kwargs):
    return SimpleS3RetryPolicy(RecordingSleeps(), rng=random.Random(0), **kwargs)


def run(aw):
    return lang.sync_await(aw)


def test_read_failures():
    c = CannedAsyncHttpClient(err(500, 'InternalError'))
    with pytest.raises(blobs.BlobTransportError):
        run(_store(c).head('k'))
    assert len(c.requests) == 1

    c = CannedAsyncHttpClient(TimeoutError(), err(500, 'InternalError'), (200, {
        'ETag': '"e"',
        'Content-Length': '0',
        'Last-Modified': 'Wed, 28 Oct 2009 22:32:00 GMT',
    }, b''))
    p = _policy()
    assert run(_store(c, policy=p).head('k')).version == blobs.BlobVersion('"e"')
    assert len(c.requests) == 3
    assert len(p._sleeps.delays) == 2  # noqa

    c = CannedAsyncHttpClient(*[err(500, 'InternalError')] * 3)
    with pytest.raises(blobs.BlobTransportError):
        run(_store(c, policy=_policy(max_attempts=3)).head('k'))
    assert len(c.requests) == 3


def test_ambiguous_conditional_write_never_retried():
    for fail in [TimeoutError(), err(500, 'InternalError'), err(503, 'ServiceUnavailable')]:
        c = CannedAsyncHttpClient(fail, OK_PUT)
        with pytest.raises(blobs.BlobIndeterminateError) as ei:
            run(_store(c, policy=_policy()).put('k', b'x', cond=blobs.IfAbsent()))
        assert type(ei.value) is blobs.BlobIndeterminateError
        assert len(c.requests) == 1


def test_ambiguous_unconditional_write():
    c = CannedAsyncHttpClient(TimeoutError())
    with pytest.raises(blobs.BlobIndeterminateError):
        run(_store(c).put('k', b'x'))

    c = CannedAsyncHttpClient(TimeoutError(), OK_PUT)
    assert run(_store(c, policy=_policy()).put('k', b'x')) == blobs.BlobVersion('"e"')
    assert len(c.requests) == 2


def test_not_applied():
    c = CannedAsyncHttpClient(err(409, 'ConditionalRequestConflict'))
    with pytest.raises(blobs.BlobConflictError):
        run(_store(c).put('k', b'x', cond=blobs.IfAbsent()))

    c = CannedAsyncHttpClient(err(409, 'ConditionalRequestConflict'), ConnectionRefusedError(), OK_PUT)
    assert run(_store(c, policy=_policy()).put('k', b'x', cond=blobs.IfAbsent())) == blobs.BlobVersion('"e"')
    assert len(c.requests) == 3

    c = CannedAsyncHttpClient(ConnectionRefusedError())
    with pytest.raises(blobs.BlobTransportError):
        run(_store(c).put('k', b'x', cond=blobs.IfAbsent()))


def test_throttled():
    c = CannedAsyncHttpClient(err(503, 'SlowDown'))
    with pytest.raises(blobs.BlobThrottledError):
        run(_store(c).put('k', b'x', cond=blobs.IfAbsent()))

    c = CannedAsyncHttpClient(err(503, 'SlowDown'), OK_PUT)
    assert run(_store(c, policy=_policy()).put('k', b'x', cond=blobs.IfAbsent())) == blobs.BlobVersion('"e"')

    c = CannedAsyncHttpClient(err(503, 'SlowDown'), OK_PUT)
    with pytest.raises(blobs.BlobThrottledError):
        run(_store(c, policy=_policy(no_throttled=True)).put('k', b'x'))


def test_terminal_not_retried():
    c = CannedAsyncHttpClient(err(403, 'AccessDenied'))
    with pytest.raises(blobs.BlobStoreError) as ei:
        run(_store(c, policy=_policy()).get('k'))
    assert ei.value.code == 'AccessDenied'  # type: ignore[attr-defined]
    assert len(c.requests) == 1


def test_200_with_error():
    copy_ok: tuple = (200, {}, b'<CopyObjectResult><ETag>"c"</ETag></CopyObjectResult>')
    c = CannedAsyncHttpClient((200, {}, b'<?xml version="1.0"?>\n<Error><Code>InternalError</Code></Error>'), copy_ok)
    assert run(_store(c, policy=_policy()).copy('a', 'b')) == blobs.BlobVersion('"c"')
    assert len(c.requests) == 2

    # A conditional copy answered 200-with-InternalError is ambiguous, so never retried.
    c = CannedAsyncHttpClient((200, {}, b'<Error><Code>InternalError</Code></Error>'), copy_ok)
    all_caps = S3BlobStore.Config(capabilities=blobs.ALL_BLOB_CAPABILITIES)
    with pytest.raises(blobs.BlobIndeterminateError):
        run(_store(c, policy=_policy(), config=all_caps).copy('a', 'b', cond=blobs.IfAbsent()))
    assert len(c.requests) == 1

    c = CannedAsyncHttpClient((200, {}, b'<Error><Code>AccessDenied</Code></Error>'))
    with pytest.raises(blobs.BlobStoreError) as ei:
        run(_store(c, policy=_policy()).copy('a', 'b'))
    assert ei.value.code == 'AccessDenied'  # type: ignore[attr-defined]


def test_complete_after_ambiguous():
    c = CannedAsyncHttpClient(err(500, 'InternalError'), err(404, 'NoSuchUpload'))
    st = _store(c, policy=_policy())
    with pytest.raises(blobs.BlobIndeterminateError):
        run(st.complete_multipart_upload('k', 'u', [(1, '"p"')]))
    assert len(c.requests) == 2

    c = CannedAsyncHttpClient(err(404, 'NoSuchUpload'))
    with pytest.raises(blobs.BlobStoreError) as ei:
        run(_store(c).complete_multipart_upload('k', 'u', [(1, '"p"')]))
    assert not isinstance(ei.value, blobs.BlobIndeterminateError)


def test_not_implemented_condition():
    c = CannedAsyncHttpClient(err(501, 'NotImplemented'))
    with pytest.raises(blobs.UnsupportedBlobOperationError):
        run(_store(c).put('k', b'x', cond=blobs.IfMatch(blobs.BlobVersion('"v"'))))


def test_checks_before_io():
    c = CannedAsyncHttpClient()
    st = _store(c, config=S3BlobStore.Config(capabilities=blobs.BlobCapability.PUT_IF_ABSENT))
    with pytest.raises(blobs.UnsupportedBlobOperationError):
        run(st.put('k', b'', cond=blobs.IfMatch(blobs.BlobVersion('"v"'))))
    with pytest.raises(blobs.UnsupportedBlobOperationError):
        run(st.copy('a', 'b', cond=blobs.IfAbsent()))
    with pytest.raises(blobs.InvalidBlobKeyError):
        run(st.get('a//b'))
    with pytest.raises(ValueError):  # noqa
        run(st.copy('a', 'a'))
    assert c.requests == []
