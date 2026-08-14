import typing as ta

from ... import check
from ... import dataclasses as dc
from ...http.pipelines.requests import FullIoPipelineHttpRequest
from ...http.pipelines.responses import FullIoPipelineHttpResponse
from ...io.streambufs.utils import ByteStreamBuffers
from ...logs import all as logs


log = logs.get_module_logger(globals())


##


class HttpHandler(ta.Protocol):
    def __call__(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        raise NotImplementedError


@dc.dataclass(frozen=True, kw_only=True)
class HttpHealthConfig:
    path: str = '/healthz'
    method: str = 'GET'
    healthy_body: bytes = b'ready'
    shutting_down_body: bytes = b'shutting down'

    def __post_init__(self) -> None:
        check.arg(self.path.startswith('/'))
        check.non_empty_str(self.method)

    def matches(self, request: FullIoPipelineHttpRequest) -> bool:
        path, _, _ = request.head.target.partition('?')
        return request.head.method.upper() == self.method.upper() and path == self.path

    def response(self, *, healthy: bool) -> FullIoPipelineHttpResponse:
        return FullIoPipelineHttpResponse.simple(
            status=200 if healthy else 503,
            body=self.healthy_body if healthy else self.shutting_down_body,
        )


class HttpRequestDispatcher:
    """Route health checks separately from application request execution."""

    def __init__(
            self,
            handler: HttpHandler,
            *,
            health: HttpHealthConfig | None,
    ) -> None:
        super().__init__()

        self._handler = handler
        self._health = health

    def is_health_request(self, request: FullIoPipelineHttpRequest) -> bool:
        return self._health is not None and self._health.matches(request)

    def health_response(
            self,
            request: FullIoPipelineHttpRequest,
            *,
            healthy: bool,
    ) -> FullIoPipelineHttpResponse:
        health = check.not_none(self._health)
        check.arg(health.matches(request))
        return health.response(healthy=healthy)

    def dispatch(self, request: FullIoPipelineHttpRequest) -> FullIoPipelineHttpResponse:
        try:
            response = self._handler(request)
            check.isinstance(response, FullIoPipelineHttpResponse)
            ByteStreamBuffers.bytes_len(response.body)
            return response
        except BaseException as exc:  # noqa
            log.exception(exc)  # noqa: TRY401
            return FullIoPipelineHttpResponse.simple(
                status=500,
                body=b'internal server error',
            )
