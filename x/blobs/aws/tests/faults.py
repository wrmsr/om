"""
Transport-level fault injection around a *real* http client: raising before or after actually sending a request, or
answering with a synthesized error response without sending it. Emulates no S3 behavior.
"""
import re
import threading
import typing as ta
import urllib.parse

from omcore import dataclasses as dc
from omcore.http import all as http
from omcore.io.readers import AsyncBytesReaders


##


class HttpFaultAction:
    pass


@dc.dataclass(frozen=True)
class RaiseBefore(HttpFaultAction):
    """Raise HttpClientError without sending. The default cause is a timeout."""

    cause: ta.Callable[[], BaseException] = TimeoutError


@dc.dataclass(frozen=True)
class RaiseAfter(HttpFaultAction):
    """Send the request for real, discard the response, then raise HttpClientError as if it had timed out."""

    cause: ta.Callable[[], BaseException] = TimeoutError


def refuse() -> RaiseBefore:
    return RaiseBefore(ConnectionRefusedError)


@dc.dataclass(frozen=True)
class Respond(HttpFaultAction):
    """Answer with an S3-style XML error response without sending."""

    status: int
    code: str
    message: str = 'injected'
    after: bool = False  # send for real first, then answer with the error regardless


@dc.dataclass(frozen=True, kw_only=True)
class HttpFault:
    action: HttpFaultAction
    method: str | None = None
    path: str | re.Pattern[str] | None = None  # matched against the url path, e.g. re.compile(r'.*/manifest/\d+')
    query: str | None = None  # a query parameter name which must be present, e.g. 'uploadId'
    no_query: bool = False  # require no query string at all
    nth: int = 0

    def matches(self, req: http.HttpClientRequest) -> bool:
        u = urllib.parse.urlsplit(req.url)
        if self.method is not None and req.method_or_default != self.method:
            return False
        if self.path is not None:
            if isinstance(self.path, str):
                if u.path != self.path:
                    return False
            elif self.path.fullmatch(u.path) is None:
                return False
        names = {p.partition('=')[0] for p in u.query.split('&') if p}
        if self.query is not None and self.query not in names:
            return False
        if self.no_query and names:  # noqa
            return False
        return True


class FaultInjectingAsyncHttpClient(http.AsyncHttpClient):
    def __init__(self, inner: http.AsyncHttpClient, faults: ta.Iterable[HttpFault] = ()) -> None:
        super().__init__()

        self._inner = inner
        self._lock = threading.Lock()
        self._faults: list[list[ta.Any]] = [[f, 0, False] for f in faults]

    def add(self, fault: HttpFault) -> None:
        with self._lock:
            self._faults.append([fault, 0, False])

    def pending(self) -> list[HttpFault]:
        with self._lock:
            return [f for f, _, fired in self._faults if not fired]

    def _match(self, req: http.HttpClientRequest) -> HttpFault | None:
        with self._lock:
            for st in self._faults:
                f, seen, fired = st
                if fired or not f.matches(req):
                    continue
                st[1] = seen + 1
                if seen == f.nth:
                    st[2] = True
                    return f
        return None

    async def _stream_request(
            self,
            ctx: http.HttpClientContext,
            req: http.HttpClientRequest,
    ) -> http.AsyncStreamHttpClientResponse:
        if (f := self._match(req)) is None:
            return await self._inner.stream_request(req, context=ctx)

        a = f.action
        if isinstance(a, RaiseBefore):
            raise http.HttpClientError from a.cause()

        if isinstance(a, RaiseAfter):
            await self._inner.request(req, context=ctx)
            raise http.HttpClientError from a.cause()

        if isinstance(a, Respond):
            if a.after:
                await self._inner.request(req, context=ctx)
            body = (
                f'<?xml version="1.0" encoding="UTF-8"?>'
                f'<Error><Code>{a.code}</Code><Message>{a.message}</Message></Error>'
            ).encode()
            return http.AsyncStreamHttpClientResponse(
                status=a.status,
                headers=http.HttpHeaders({'Content-Type': 'application/xml', 'Content-Length': str(len(body))}),
                request=req,
                _stream=AsyncBytesReaders.of_bytes(body),
            )

        raise TypeError(a)


##


@dc.dataclass(frozen=True, kw_only=True)
class RecordedRequest:
    method: str
    url: str
    headers: ta.Mapping[str, ta.Sequence[str]]

    @property
    def path(self) -> str:
        return urllib.parse.urlsplit(self.url).path

    @property
    def query(self) -> str:
        return urllib.parse.urlsplit(self.url).query

    def header(self, name: str) -> str | None:
        for k, vs in self.headers.items():
            if k.lower() == name.lower():
                return vs[0]
        return None


class RecordingAsyncHttpClient(http.AsyncHttpClient):
    def __init__(self, inner: http.AsyncHttpClient) -> None:
        super().__init__()

        self._inner = inner
        self._lock = threading.Lock()
        self._requests: list[RecordedRequest] = []
        self._no_decompress: list[bool] = []

    def requests(self) -> list[RecordedRequest]:
        with self._lock:
            return list(self._requests)

    def clear(self) -> None:
        with self._lock:
            self._requests.clear()

    async def _stream_request(
            self,
            ctx: http.HttpClientContext,
            req: http.HttpClientRequest,
    ) -> http.AsyncStreamHttpClientResponse:
        with self._lock:
            self._requests.append(RecordedRequest(
                method=req.method_or_default,
                url=req.url,
                headers={**(req.headers_ or {}), **({'x-test-no-decompress': ['1']} if req.no_decompress else {})},
            ))
        return await self._inner.stream_request(req, context=ctx)
