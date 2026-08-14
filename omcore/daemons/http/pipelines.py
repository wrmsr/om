import typing as ta

from ... import dataclasses as dc
from ...http.pipelines.aggregators import IoPipelineHttpAggregationConfig
from ...http.pipelines.requests import FullIoPipelineHttpRequest
from ...http.pipelines.requests import IoPipelineHttpRequestAborted
from ...http.pipelines.responses import FullIoPipelineHttpResponse
from ...http.pipelines.servers.requests import IoPipelineHttpRequestAggregatorDecoder
from ...http.pipelines.servers.requests import IoPipelineHttpRequestDecoder
from ...http.pipelines.servers.responses import IoPipelineHttpResponseEncoder
from ...io.pipelines.core import IoPipeline
from ...io.pipelines.core import IoPipelineHandler
from ...io.pipelines.core import IoPipelineHandlerContext
from ...io.pipelines.core import IoPipelineMessages
from ...io.pipelines.flow.stub import StubIoPipelineFlowService
from ...io.pipelines.flow.types import IoPipelineFlow


##


@dc.dataclass(frozen=True, kw_only=True)
class HttpServerRequest:
    request: FullIoPipelineHttpRequest


@dc.dataclass(frozen=True, kw_only=True)
class HttpServerSendResponse:
    response: FullIoPipelineHttpResponse


@dc.dataclass(frozen=True, kw_only=True)
class HttpPipelineFailure:
    exc: BaseException


##


class HttpServerSessionIoPipelineHandler(IoPipelineHandler):
    """Expose one aggregated HTTP request and accept one full response command."""

    def __init__(self) -> None:
        super().__init__()

        self._state: ta.Literal['new', 'ready', 'dispatch', 'response', 'done'] = 'new'

    def _state_is(self, state: str) -> bool:
        return self._state == state

    def _fail(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        if self._state == 'done':
            return
        self._state = 'done'
        ctx.feed_out(HttpPipelineFailure(exc=exc))
        ctx.feed_final_output()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            if self._state != 'new':
                raise RuntimeError('HTTP server received duplicate initial input')
            self._state = 'ready'
            ctx.mark_propagated('inbound', msg)
            return

        if isinstance(msg, FullIoPipelineHttpRequest):
            if self._state != 'ready':
                self._fail(ctx, RuntimeError('Unexpected HTTP request'))
                return
            self._state = 'dispatch'
            ctx.feed_out(HttpServerRequest(request=msg))
            return

        if isinstance(msg, IoPipelineHttpRequestAborted):
            exc = msg.reason if isinstance(msg.reason, BaseException) else RuntimeError(msg.reason)
            self._fail(ctx, exc)
            return

        if isinstance(msg, HttpServerSendResponse):
            if self._state != 'dispatch':
                raise RuntimeError('HTTP server has no request awaiting a response')
            self._state = 'response'
            ctx.feed_out(msg.response)
            if not self._state_is('response'):
                return
            self._state = 'done'
            IoPipelineFlow.maybe_flush_output(ctx)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self._fail(ctx, msg.exc)
            return

        if isinstance(msg, HttpPipelineFailure):
            self._fail(ctx, msg.exc)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            if self._state != 'done':
                self._fail(ctx, EOFError('HTTP connection closed'))
                ctx.mark_propagated('inbound', msg)
                return
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)


def pipeline_http_server_spec(
        *,
        max_request_body_bytes: int = 64 * 1024,
) -> IoPipeline.Spec:
    if max_request_body_bytes < 0:
        raise ValueError(max_request_body_bytes)

    aggregation_config = IoPipelineHttpAggregationConfig(
        body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(
            max_size=max_request_body_bytes,
            chunk_size=max(1, min(64 * 1024, max_request_body_bytes or 1)),
        ),
    )
    return IoPipeline.Spec(
        handlers=[
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestAggregatorDecoder(config=aggregation_config),
            IoPipelineHttpResponseEncoder(),
            HttpServerSessionIoPipelineHandler(),
        ],
        services=[StubIoPipelineFlowService()],
    )
