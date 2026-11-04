# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
An optional handler closing a connection once it has answered a given number of requests: one request per connection,
for a server whose clients connect per call.

Installed between the envelope codec and the session. Once the last allowed request's answer has gone out it asks the
session for a graceful close, which flushes that answer and completes output. A request beyond the allowance is a
protocol violation and fails the connection.
"""
import typing as ta

from ..io.pipelines.core import IoPipelineHandler
from ..io.pipelines.core import IoPipelineHandlerContext
from ..io.pipelines.core import IoPipelineMessages
from .errors import RpcProtocolError
from .messages import RpcErrorMessage
from .messages import RpcRequestMessage
from .messages import RpcResultMessage
from .messages import RpcSessionMessages


##


class RpcCloseAfterRequestsIoPipelineHandler(IoPipelineHandler):
    def __init__(self, max_requests: int = 1) -> None:
        super().__init__()

        if max_requests < 1:
            raise ValueError(max_requests)
        self._max_requests = max_requests

        self._received = 0
        self._answered = 0
        self._closing = False

    @property
    def received(self) -> int:
        return self._received

    @property
    def answered(self) -> int:
        return self._answered

    @staticmethod
    def _request_close(ctx: IoPipelineHandlerContext) -> None:
        if not ctx.invalidated:
            ctx.feed_in(RpcSessionMessages.Close())

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcRequestMessage):
            self._received += 1
            if self._received > self._max_requests:
                ctx.feed_in(IoPipelineMessages.Error(
                    RpcProtocolError(f'more than {self._max_requests} request(s) on one connection'),
                    direction='inbound',
                    handler=ctx.ref,
                ))
                return

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)

        if isinstance(msg, (RpcResultMessage, RpcErrorMessage)):
            self._answered += 1
            if self._answered >= self._max_requests and not self._closing and not ctx.invalidated:
                self._closing = True
                # Deferred, so the session finishes sending the answer before it hears of the close.
                ctx.defer(self._request_close)
