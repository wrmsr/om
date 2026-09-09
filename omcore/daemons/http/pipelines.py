import typing as ta

from ... import dataclasses as dc
from ...http.pipelines.aggregators import IoPipelineHttpAggregationConfig
from ...http.pipelines.requests import FullIoPipelineHttpRequest
from ...http.pipelines.requests import IoPipelineHttpRequestAborted
from ...http.pipelines.responses import FullIoPipelineHttpResponse
from ...http.pipelines.servers.requests import IoPipelineHttpRequestAggregatorDecoder
from ...http.pipelines.servers.requests import IoPipelineHttpRequestDecoder
from ...http.pipelines.servers.responses import IoPipelineHttpResponseEncoder
from ...io.pipelines import all as ipl


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


class HttpServerSessionIoPipelineHandler(ipl.Handler):
    """Expose one aggregated HTTP request and accept one full response command."""

    def __init__(self) -> None:
        super().__init__()

        self._state: ta.Literal['new', 'ready', 'dispatch', 'response', 'done'] = 'new'

    def _state_is(self, state: str) -> bool:
        return self._state == state

    def _fail(self, ctx: ipl.HandlerContext, exc: BaseException) -> None:
        if self._state == 'done':
            return
        self._state = 'done'
        ctx.feed_out(HttpPipelineFailure(exc=exc))
        ctx.feed_final_output()

    def inbound(self, ctx: ipl.HandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, ipl.Messages.InitialInput):
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
            ipl.Flow.maybe_flush_output(ctx)
            ctx.feed_final_output()
            return

        if isinstance(msg, ipl.Messages.Error):
            self._fail(ctx, msg.exc)
            return

        if isinstance(msg, HttpPipelineFailure):
            self._fail(ctx, msg.exc)
            return

        if isinstance(msg, ipl.Messages.FinalInput):
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
) -> ipl.Pipeline.Spec:
    if max_request_body_bytes < 0:
        raise ValueError(max_request_body_bytes)

    aggregation_config = IoPipelineHttpAggregationConfig(
        body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(
            max_size=max_request_body_bytes,
            chunk_size=max(1, min(64 * 1024, max_request_body_bytes or 1)),
        ),
    )
    return ipl.Pipeline.Spec(
        handlers=[
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestAggregatorDecoder(config=aggregation_config),
            IoPipelineHttpResponseEncoder(),
            HttpServerSessionIoPipelineHandler(),
        ],
        services=[ipl.StubFlowService()],
    )
