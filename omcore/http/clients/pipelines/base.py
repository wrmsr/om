# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import dataclasses as dc
import errno
import socket
import typing as ta
import urllib.parse

from ....io.pipelines.bytes.buffers import OutboundBytesBufferIoPipelineHandler
from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.flow.stub import StubIoPipelineFlowService
from ....io.pipelines.handlers.logs import LoggingIoPipelineHandler
from ....io.pipelines.ssl.handlers import SslIoPipelineHandler
from ....io.streambufs.utils import ByteStreamBuffers
from ....lite.abstract import Abstract
from ....lite.check import check
from ...clients.base import BaseHttpClient
from ...clients.base import HttpClientError
from ...clients.base import HttpClientRequest
from ...headers import HttpHeaders
from ...pipelines.clients.clients import IoPipelineHttpClientHandler
from ...pipelines.clients.requests import IoPipelineHttpRequestCompressor
from ...pipelines.clients.requests import IoPipelineHttpRequestEncoder
from ...pipelines.clients.responses import IoPipelineHttpClientResponseDecoder
from ...pipelines.clients.responses import IoPipelineHttpResponseAggregatorDecoder
from ...pipelines.clients.responses import IoPipelineHttpResponseDechunker
from ...pipelines.clients.responses import IoPipelineHttpResponseDecompressor
from ...pipelines.clients.timeouts import IoPipelineHttpClientRequestTimeoutHandler
from ...pipelines.requests import FullIoPipelineHttpRequest
from ...pipelines.responses import IoPipelineHttpResponseAborted


BaseIoPipelineHttpClientConfigT = ta.TypeVar('BaseIoPipelineHttpClientConfigT', bound='BaseIoPipelineHttpClient.Config')


##


class _IoPipelineHttpResponseReaderState:
    def __init__(self) -> None:
        super().__init__()

        self._pending = b''
        self._pending_pos = 0
        self._done = False

    def read_pending(self, n: int) -> ta.Optional[bytes]:
        if n == 0 or self._done:
            return b''
        if self._pending_pos >= len(self._pending):
            return None

        remaining = len(self._pending) - self._pending_pos
        if n < 0 or n >= remaining:
            out = self._pending[self._pending_pos:]
            self._pending = b''
            self._pending_pos = 0
            return out

        out = self._pending[self._pending_pos:self._pending_pos + n]
        self._pending_pos += n
        return out

    def feed_data(self, data: ta.Any, n: int) -> bytes:
        if self._done or self._pending_pos < len(self._pending):
            raise RuntimeError('invalid response reader state')

        self._pending = ByteStreamBuffers.to_bytes(data, strict=True)
        self._pending_pos = 0
        if not self._pending:
            raise RuntimeError('empty HTTP response body data')
        return check.not_none(self.read_pending(n))

    def feed_end(self) -> bytes:
        if self._pending_pos < len(self._pending):
            raise RuntimeError('HTTP response ended with pending reader data')
        self._done = True
        return b''


def _raise_http_response_aborted(msg: IoPipelineHttpResponseAborted) -> ta.NoReturn:
    exc = HttpClientError(f'HTTP response aborted: {msg.reason_str}')
    if isinstance(msg.reason, BaseException):
        raise exc from msg.reason
    raise exc


##


class BaseIoPipelineHttpClient(BaseHttpClient, Abstract, ta.Generic[BaseIoPipelineHttpClientConfigT]):
    @dc.dataclass(frozen=True)
    class Config:
        connect_timeout_s: ta.Optional[float] = 3.
        request_timeout_s: ta.Optional[float] = None

    def __init__(
            self,
            config: BaseIoPipelineHttpClientConfigT,
            **pipeline_kwargs: ta.Any,
    ) -> None:
        super().__init__()

        self._config = config
        self._pipeline_kwargs = pipeline_kwargs

    @property
    def config(self) -> BaseIoPipelineHttpClientConfigT:
        return self._config

    #

    @dc.dataclass(frozen=True)
    class ParsedUrl:
        host: str
        port: int
        path: str
        authority: str

        is_ssl: bool = False

    @classmethod
    def parse_url(cls, url: str) -> ParsedUrl:
        parsed = urllib.parse.urlsplit(url)

        if parsed.scheme == 'http':
            default_port = 80
            is_ssl = False
        elif parsed.scheme == 'https':
            default_port = 443
            is_ssl = True
        else:
            raise ValueError(url)

        if parsed.username is not None or parsed.password is not None:
            raise ValueError('URL userinfo is not supported')

        host = parsed.hostname
        if not host:
            raise ValueError('URL host is required')

        explicit_port = parsed.port
        port = explicit_port if explicit_port is not None else default_port
        if not 1 <= port <= 65535:
            raise ValueError(f'invalid URL port: {port}')

        authority_host = f'[{host}]' if ':' in host else host
        authority = (
            f'{authority_host}:{explicit_port}'
            if explicit_port is not None else
            authority_host
        )

        path = parsed.path or '/'
        if parsed.query:
            path += f'?{parsed.query}'

        return cls.ParsedUrl(
            host,
            port,
            path,
            authority,
            is_ssl=is_ssl,
        )

    #

    _aggregate_responses: bool = False  # FIXME: jank placeholder lol

    def _build_pipeline_spec(
            self,
            *,
            outermost_handlers: ta.Optional[ta.Sequence[IoPipelineHandler]] = None,
            innermost_handlers: ta.Optional[ta.Sequence[IoPipelineHandler]] = None,

            with_logging: bool = False,

            with_ssl: bool = False,
            ssl_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,

            without_flow: bool = False,
            flow_auto_read: bool = False,

            raise_immediately: bool = False,

            request_timeout_s: ta.Optional[float] = None,
    ) -> IoPipeline.Spec:
        return IoPipeline.Spec(
            [
                *(outermost_handlers or []),

                *([LoggingIoPipelineHandler()] if with_logging else []),

                *([OutboundBytesBufferIoPipelineHandler()] if not without_flow else []),

                *([SslIoPipelineHandler(**(ssl_kwargs or {}))] if with_ssl else []),

                IoPipelineHttpRequestEncoder(),

                IoPipelineHttpClientResponseDecoder(),
                *([IoPipelineHttpResponseDechunker()] if not self._aggregate_responses else []),
                IoPipelineHttpResponseDecompressor(),
                *([IoPipelineHttpResponseAggregatorDecoder()] if self._aggregate_responses else []),

                IoPipelineHttpRequestCompressor(),

                *(
                    [IoPipelineHttpClientRequestTimeoutHandler(request_timeout_s)]
                    if request_timeout_s is not None else []
                ),
                IoPipelineHttpClientHandler(),

                *(innermost_handlers or []),
            ],

            config=IoPipeline.Config.DEFAULT.update(
                raise_immediately=raise_immediately,
            ),

            services=[
                *([StubIoPipelineFlowService(auto_read=flow_auto_read)] if not without_flow else []),
            ],
        )

    #

    @dc.dataclass(frozen=True)
    class _PreparedRequest:
        parsed_url: 'BaseIoPipelineHttpClient.ParsedUrl'
        full_request: FullIoPipelineHttpRequest
        pipeline_spec: IoPipeline.Spec

    def _prepare_request(
            self,
            req: HttpClientRequest,
            **pipeline_kwargs: ta.Any,
    ) -> _PreparedRequest:
        parsed_url = self.parse_url(req.url)

        data: bytes
        if isinstance(req.data, bytes):
            data = req.data
        elif isinstance(req.data, str):
            data = req.data.encode('utf-8')  # FIXME: lol
        elif req.data is None:
            data = b''
        else:
            raise TypeError(req.data)

        full_request = FullIoPipelineHttpRequest.simple(
            parsed_url.authority,
            parsed_url.path,
            method=req.method_or_default,
            headers=HttpHeaders.of(req.headers_).update(
                ('User-Agent', 'omcore-http-client/0.1'),
                if_present='skip',
            ),
            body=data,
        )

        merged_pipeline_kwargs = {
            **self._pipeline_kwargs,
            **pipeline_kwargs,
            'request_timeout_s': (
                req.timeout_s
                if req.timeout_s is not None else self._config.request_timeout_s
            ),
        }

        pipeline_spec = self._build_pipeline_spec(
            **(dict(  # type: ignore[arg-type]
                with_ssl=True,
                ssl_kwargs=dict(
                    server_side=False,
                    server_hostname=parsed_url.host,
                ),
            ) if parsed_url.is_ssl else {}),

            **merged_pipeline_kwargs,
        )

        return self._PreparedRequest(
            parsed_url,
            full_request,
            pipeline_spec,
        )

    #

    def _try_set_nodelay(self, sock: 'socket.socket') -> None:
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError as e:
            if e.errno != errno.ENOPROTOOPT:
                raise
