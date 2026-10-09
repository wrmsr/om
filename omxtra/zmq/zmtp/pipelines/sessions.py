"""
The session bridge: the innermost stage of a connection, joining it to the endpoint which owns its peer.

The endpoint never calls into a pipeline. It notifies the connection's owner through a PeerSink, and the owner feeds a
ZmtpSessionWake into the pipeline - through the driver's own entry point - for this stage to act on in the pipeline's
turn. Output is pulled from the endpoint while the transport is writable, at most a budget per turn, continuing through
a Defer so the driver can report output pressure in between. Input is requested after each batch only while the endpoint
has room for the peer's messages; otherwise reading resumes on a wake once room returns.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.flow.types import IoPipelineFlow
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages

from ...core.endpoints import Endpoint
from ...core.peers import Peer
from ...core.peers import PeerSink
from ...core.queues import message_size
from ..commands import ZmtpCommand
from .messages import ZmtpMessage
from .messages import ZmtpPeerReady


##


@dc.dataclass(frozen=True)
class ZmtpSessionWake:
    """Fed into a connection's pipeline by its owner, on its endpoint's behalf."""

    kind: ta.Literal['send', 'recv']


@dc.dataclass(frozen=True)
class ZmtpSessionEnded:
    """
    Emitted outbound to the connection's owner when the peer ended the connection. Not ordered behind output waiting to
    be written, so the owner learns of it at once - and ends the connection, abortively: a peer which closed reads no
    more, and output it will never read must not hold the connection open.
    """


class ZmtpSessionIoPipelineHandler(IoPipelineHandler):
    def __init__(
            self,
            endpoint: Endpoint,
            sink: PeerSink,
            *,
            turn_output_budget: int = 64 * 1024,
    ) -> None:
        super().__init__()

        if turn_output_budget < 1:
            raise ValueError(turn_output_budget)

        self._endpoint = endpoint
        self._sink: PeerSink | None = sink
        self._turn_output_budget = turn_output_budget

        self._peer: Peer | None = None
        self._was_ready = False
        self._ended = False
        self._failure: BaseException | None = None

        self._writable = True
        self._received = False
        self._read_paused = False
        self._continuation_pending = False

    @property
    def peer(self) -> Peer | None:
        return self._peer

    @property
    def was_ready(self) -> bool:
        """Whether the connection completed its handshake and was attached to the endpoint."""

        return self._was_ready

    @property
    def failure(self) -> BaseException | None:
        return self._failure

    #

    def _request_read(self, ctx: IoPipelineHandlerContext) -> None:
        if (flow := ctx.services.find(IoPipelineFlow)) is not None and not flow.is_auto_read():
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _end(self, exc: BaseException | None = None) -> None:
        if exc is not None and self._failure is None:
            self._failure = exc
        self._ended = True
        # The sink is typically the connection's owner, which holds the driver: dropping it - and the peer, which holds
        # it too - leaves no cycle through the pipeline.
        self._sink = None
        if (peer := self._peer) is not None:
            self._peer = None
            self._endpoint.detach(peer)

    @staticmethod
    def _resume(ctx: IoPipelineHandlerContext) -> None:
        h = check.isinstance(ctx.handler, ZmtpSessionIoPipelineHandler)
        h._continuation_pending = False  # noqa
        h._pump(ctx)  # noqa

    def _pump(self, ctx: IoPipelineHandlerContext) -> None:
        if self._continuation_pending:
            return

        budget = self._turn_output_budget
        while self._writable and (peer := self._peer) is not None:
            if budget <= 0:
                self._continuation_pending = True
                ctx.defer(ZmtpSessionIoPipelineHandler._resume)
                return

            if (msg := self._endpoint.take_output(peer)) is None:
                return

            ctx.feed_out(ZmtpMessage(msg))
            # Frames count too, so a run of empty messages is bounded as well.
            budget -= message_size(msg) + len(msg)

    def _on_ready(self, ctx: IoPipelineHandlerContext, ready: ZmtpPeerReady) -> None:
        check.state(self._peer is None and not self._ended)
        self._peer = self._endpoint.attach(
            socket_type=ready.socket_type,
            identity=ready.identity,
            sink=check.not_none(self._sink),
        )
        self._was_ready = True
        self._pump(ctx)

    def _on_flush_input(self, ctx: IoPipelineHandlerContext) -> None:
        if self._received and (peer := self._peer) is not None:
            if self._endpoint.can_receive(peer):
                self._request_read(ctx)
            else:
                self._read_paused = True
        self._received = False

    def _on_wake(self, ctx: IoPipelineHandlerContext, wake: ZmtpSessionWake) -> None:
        if wake.kind == 'send':
            self._pump(ctx)

        elif wake.kind == 'recv':
            if self._read_paused and (peer := self._peer) is not None and self._endpoint.can_receive(peer):
                self._read_paused = False
                self._request_read(ctx)

        else:
            raise TypeError(wake)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Removed):
            # Removed without ending - the pipeline was destroyed: the connection is gone all the same.
            self._end()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, ZmtpMessage):
            self._received = True
            if (peer := self._peer) is not None:
                self._endpoint.deliver(peer, msg.frames)

        elif isinstance(msg, ZmtpCommand):
            # Ignored, but input all the same.
            self._received = True

        elif isinstance(msg, ZmtpSessionWake):
            self._on_wake(ctx, msg)

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._on_flush_input(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, ZmtpPeerReady):
            self._received = True
            try:
                self._on_ready(ctx, msg)
            except BaseException as e:
                self._end(e)
                raise

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._writable = True
            self._pump(ctx)

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._writable = False

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            was_ended = self._ended
            self._end()
            ctx.feed_in(msg)
            if not was_ended:
                ctx.feed_out(ZmtpSessionEnded())

        elif isinstance(msg, IoPipelineMessages.Error):
            # Not swallowed: recorded once for the owner, then left to fail the connection.
            self._end(msg.exc)
            ctx.feed_in(msg)

        else:
            ctx.feed_in(msg)
