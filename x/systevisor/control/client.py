# ruff: noqa: UP006 UP007 UP037 UP045
import dataclasses as dc
import socket
import typing as ta
import urllib.parse

from omcore.http.pipelines.clients.requests import IoPipelineHttpRequestEncoder
from omcore.http.pipelines.clients.responses import IoPipelineHttpClientResponseDecoder
from omcore.http.pipelines.clients.responses import IoPipelineHttpResponseDechunker
from omcore.http.pipelines.requests import FullIoPipelineHttpRequest
from omcore.http.pipelines.responses import IoPipelineHttpResponseAborted
from omcore.http.pipelines.responses import IoPipelineHttpResponseBodyData
from omcore.http.pipelines.responses import IoPipelineHttpResponseEnd
from omcore.http.pipelines.responses import IoPipelineHttpResponseHead
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from omcore.io.streambufs.utils import ByteStreamBuffers

from .jsoncodec import SystevisorJsonCodec


@dc.dataclass(frozen=True)
class SystevisorApiEndpoint:
    unix_socket: ta.Optional[str] = None
    host: ta.Optional[str] = None
    port: ta.Optional[int] = None

    def __post_init__(self) -> None:
        unix = self.unix_socket is not None
        tcp = self.host is not None or self.port is not None
        if unix == tcp or (self.host is None) != (self.port is None):
            raise ValueError('endpoint must specify exactly one complete Unix or TCP address')

    @classmethod
    def parse(cls, value: str) -> 'SystevisorApiEndpoint':
        if value.startswith('unix:'):
            return cls(unix_socket=value[len('unix:'):])
        if value.startswith('/'):
            return cls(unix_socket=value)
        parsed = urllib.parse.urlsplit(value if '://' in value else f'http://{value}')
        if parsed.scheme != 'http' or parsed.hostname is None or parsed.port is None:
            raise ValueError(f'invalid systevisor endpoint: {value!r}')
        return cls(host=parsed.hostname, port=parsed.port)


@dc.dataclass(frozen=True)
class SystevisorApiClientResponse:
    status: int
    headers: ta.Mapping[str, str]
    body: bytes


class SystevisorApiClientIoPipelineHandler(IoPipelineHandler):
    def __init__(
            self,
            request: FullIoPipelineHttpRequest,
            on_body: ta.Optional[ta.Callable[[bytes], None]] = None,
    ) -> None:
        super().__init__()
        self._request = request
        self._on_body = on_body
        self.status: ta.Optional[int] = None
        self.headers: ta.Dict[str, str] = {}
        self.body_parts: ta.List[bytes] = []
        self.complete = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self._request)
            return
        if isinstance(msg, IoPipelineHttpResponseHead):
            self.status = msg.status
            self.headers = {name.lower(): value for name, value in msg.headers.raw}
            return
        if isinstance(msg, IoPipelineHttpResponseBodyData):
            data = bytes(ByteStreamBuffers.to_bytes(msg.data))
            if self._on_body is None:
                self.body_parts.append(data)
            else:
                self._on_body(data)
            return
        if isinstance(msg, IoPipelineHttpResponseEnd):
            self.complete = True
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineHttpResponseAborted):
            raise ConnectionError(f'HTTP response aborted: {msg!r}')
        if isinstance(msg, IoPipelineMessages.FinalInput):
            if not self.complete:
                raise ConnectionError('connection closed before HTTP response completed')
            ctx.feed_in(msg)
            return
        ctx.feed_in(msg)


class SystevisorApiClient:
    def __init__(
            self,
            endpoint: SystevisorApiEndpoint,
            json_codec: ta.Optional[SystevisorJsonCodec] = None,
            timeout_secs: float = 10.,
    ) -> None:
        if timeout_secs <= 0:
            raise ValueError(timeout_secs)
        self._endpoint = endpoint
        self._json_codec = json_codec if json_codec is not None else SystevisorJsonCodec()
        self._timeout_secs = timeout_secs

    def _connect(self, *, streaming: bool) -> socket.socket:
        if self._endpoint.unix_socket is not None:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self._timeout_secs)
            try:
                sock.connect(self._endpoint.unix_socket)
            except BaseException:
                sock.close()
                raise
        else:
            sock = socket.create_connection(
                (ta.cast(str, self._endpoint.host), ta.cast(int, self._endpoint.port)),
                timeout=self._timeout_secs,
            )
        if streaming:
            sock.settimeout(None)
        return sock

    def _make_request(
            self,
            method: str,
            target: str,
            body: ta.Optional[ta.Any],
    ) -> FullIoPipelineHttpRequest:
        encoded_body = b'' if body is None else self._json_codec.dumps(body)
        host = (
            'localhost' if self._endpoint.unix_socket is not None else
            f'{self._endpoint.host}:{self._endpoint.port}'
        )
        return FullIoPipelineHttpRequest.simple(
            host,
            target,
            method=method,
            content_type='application/json' if body is not None else None,
            body=encoded_body,
            connection='close',
        )

    @staticmethod
    def _pipeline_spec(handler: SystevisorApiClientIoPipelineHandler) -> IoPipeline.Spec:
        return IoPipeline.Spec([
            IoPipelineHttpRequestEncoder(),
            IoPipelineHttpClientResponseDecoder(),
            IoPipelineHttpResponseDechunker(),
            handler,
        ])

    def request(
            self,
            method: str,
            target: str,
            body: ta.Optional[ta.Any] = None,
    ) -> SystevisorApiClientResponse:
        request = self._make_request(method, target, body)
        handler = SystevisorApiClientIoPipelineHandler(request)
        with self._connect(streaming=False) as sock:
            driver = SyncSocketIoPipelineDriver(self._pipeline_spec(handler), sock)
            try:
                driver.loop_until_done()
            finally:
                driver.close()
        if handler.status is None or not handler.complete:
            raise ConnectionError('HTTP response was incomplete')
        return SystevisorApiClientResponse(
            status=handler.status,
            headers=handler.headers,
            body=b''.join(handler.body_parts),
        )

    def request_json(
            self,
            method: str,
            target: str,
            body: ta.Optional[ta.Any] = None,
    ) -> ta.Tuple[int, ta.Any]:
        response = self.request(method, target, body)
        return response.status, self._json_codec.loads(response.body)

    def stream(
            self,
            target: str,
            callback: ta.Callable[[bytes], None],
    ) -> int:
        request = self._make_request('GET', target, None)
        handler = SystevisorApiClientIoPipelineHandler(request, callback)
        with self._connect(streaming=True) as sock:
            driver = SyncSocketIoPipelineDriver(self._pipeline_spec(handler), sock)
            try:
                driver.loop_until_done()
            finally:
                driver.close()
        if handler.status is None:
            raise ConnectionError('HTTP response had no status')
        return handler.status
