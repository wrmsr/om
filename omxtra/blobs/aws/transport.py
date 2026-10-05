"""
Sends built S3 requests through a caller-provided AsyncHttpClient, classifies failures, and consults the retry policy.
Never retries or sleeps on its own. Ambiguous failures of conditional writes are never offered to the policy.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore.http import all as http
from ominfra.clouds.aws.models import base as _base

from ... import blobs
from .endpoints import S3Endpoint
from .endpoints import build_url
from .errors import S3FailureKind
from .errors import S3ResponseError
from .errors import classify_status
from .errors import classify_transport_error
from .errors import is_error_body
from .restxml import RestXmlError
from .restxml import deserialize_rest_xml_response
from .restxml import parse_rest_xml_error
from .restxml import serialize_rest_xml_request
from .retries import S3Failure
from .retries import S3RetryPolicy
from .signing import S3RequestSigner
from .streaming import S3StreamBody
from .streaming import S3StreamingSender
from .streaming import aws_chunked_body


##


@dc.dataclass(frozen=True, kw_only=True)
class S3Response:
    status: int
    headers: ta.Mapping[str, ta.Sequence[str]]
    body: bytes


# The transport-level failures the http clients surface. HttpClientError is the contract, but a few raw errors can still
# leak from underneath some of them.
_TRANSPORT_ERRORS: tuple[type[BaseException], ...] = (
    http.HttpClientError,
    TimeoutError,
    ConnectionError,
)

# For 200 responses carrying an <Error> body, the status the error would otherwise have had.
_ERROR_CODE_STATUSES: ta.Mapping[str, int] = {
    'InternalError': 500,
    'SlowDown': 503,
    'ServiceUnavailable': 503,
}


class S3Transport:
    def __init__(
            self,
            *,
            bucket: str,
            endpoint: S3Endpoint,
            signer: S3RequestSigner,
            http_client: http.AsyncHttpClient | None = None,
            retry_policy: S3RetryPolicy | None = None,
            streaming_sender: S3StreamingSender,
            timeout_s: float | None = None,
            unsigned_payload: bool = False,
            streaming_chunk_size: int = 64 * 1024,
    ) -> None:
        super().__init__()

        self._bucket = bucket
        self._endpoint = endpoint
        self._signer = signer
        self._http_client = http_client
        self._retry_policy = retry_policy
        self._streaming_sender = streaming_sender
        self._timeout_s = timeout_s
        self._unsigned_payload = unsigned_payload
        self._streaming_chunk_size = streaming_chunk_size

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def endpoint(self) -> S3Endpoint:
        return self._endpoint

    #

    async def _send(self, req: http.HttpClientRequest) -> S3Response:
        async with http.manage_async_client(self._http_client) as cli:
            resp = await cli.request(req)
        return S3Response(status=resp.status, headers=resp.headers or {}, body=resp.data or b'')

    async def _send_streaming(
            self,
            req: http.HttpClientRequest,
            body: ta.AsyncIterable[bytes],
    ) -> S3Response:
        async with http.manage_async_client(self._http_client) as cli:
            resp = await self._streaming_sender.send(cli, req, body)
        return S3Response(status=resp.status, headers=resp.headers or {}, body=resp.data or b'')

    async def _should_retry(self, f: S3Failure) -> bool:
        if self._retry_policy is None or f.kind == S3FailureKind.TERMINAL:
            return False
        if f.kind == S3FailureKind.AMBIGUOUS and f.conditional:
            # The invariant: a retry of a conditional write which did land would fail its precondition against itself.
            return False
        return await self._retry_policy.should_retry(f)

    @staticmethod
    def _failure_error(f: S3Failure, what: str) -> BaseException:
        match f.kind:
            case S3FailureKind.READ_FAILED:
                return blobs.BlobTransportError(what)
            case S3FailureKind.NOT_APPLIED:
                if f.status == 409:
                    return blobs.BlobConflictError(what)
                return blobs.BlobTransportError(what)
            case S3FailureKind.THROTTLED:
                return blobs.BlobThrottledError(what)
            case S3FailureKind.AMBIGUOUS:
                return blobs.BlobIndeterminateError(what)
            case _:
                raise TypeError(f.kind)

    async def execute(
            self,
            op: _base.Operation,
            shape: _base.Shape,
            *,
            conditional: bool = False,
            read: bool = False,
            extra_headers: ta.Sequence[tuple[str, str]] = (),
            xml_body: bool = False,
            content_md5: bool = False,
            no_decompress: bool = False,
            error_200: bool = False,
            stream_body: S3StreamBody | None = None,
    ) -> tuple[S3Response, ta.Any]:
        """
        Returns the response and its deserialized output shape. Raises S3ResponseError for terminal error responses,
        for the caller to map, and blob errors for retryable failures nothing retried.
        """

        rx = serialize_rest_xml_request(op, shape)
        url, host = build_url(self._endpoint, self._bucket, rx)
        headers = [*rx.headers, *extra_headers]
        what = f'{op.name} {rx.path}'

        attempt = 0
        after_ambiguous = False
        while True:
            attempt += 1

            try:
                if stream_body is not None:
                    req, chunk_signer = self._signer.sign_streaming(
                        method=rx.method,
                        url=url,
                        host=host,
                        headers=headers,
                        decoded_length=stream_body.length,
                        chunk_size=self._streaming_chunk_size,
                        timeout_s=self._timeout_s,
                    )
                    resp = await self._send_streaming(
                        req,
                        aws_chunked_body(stream_body.source, chunk_signer=chunk_signer),
                    )
                else:
                    req = self._signer.sign(
                        method=rx.method,
                        url=url,
                        host=host,
                        headers=headers,
                        body=rx.body,
                        xml_body=xml_body,
                        content_md5=content_md5,
                        unsigned_payload=self._unsigned_payload,
                        timeout_s=self._timeout_s,
                        no_decompress=no_decompress,
                    )
                    resp = await self._send(req)

            except _TRANSPORT_ERRORS as e:
                kind = classify_transport_error(e, read=read)
                f = S3Failure(op=op.name, attempt=attempt, kind=kind, conditional=conditional, cause=e)
                if kind == S3FailureKind.AMBIGUOUS:
                    after_ambiguous = True
                if stream_body is None and await self._should_retry(f):
                    continue
                raise self._failure_error(f, what) from e

            err: RestXmlError | None = None
            status = resp.status
            if 200 <= status < 300:
                if not (error_200 and is_error_body(resp.body)):
                    return resp, deserialize_rest_xml_response(
                        op,
                        status=status,
                        headers=resp.headers,
                        body=resp.body,
                    )
                err = parse_rest_xml_error(status=status, headers=resp.headers, body=resp.body)
                status = _ERROR_CODE_STATUSES.get(err.code or '', 400)
            else:
                err = parse_rest_xml_error(status=status, headers=resp.headers, body=resp.body)

            rerr = S3ResponseError.of(dc.replace(err, status=status), op=op.name, after_ambiguous=after_ambiguous)
            kind = classify_status(status, err.code, read=read)
            if kind == S3FailureKind.TERMINAL:
                raise rerr

            if kind == S3FailureKind.AMBIGUOUS:
                after_ambiguous = True
            f = S3Failure(
                op=op.name,
                attempt=attempt,
                kind=kind,
                conditional=conditional,
                status=status,
                code=err.code,
                cause=rerr,
            )
            if stream_body is None and await self._should_retry(f):
                continue
            raise self._failure_error(f, what) from rerr
