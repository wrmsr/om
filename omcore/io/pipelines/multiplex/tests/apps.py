# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""Child-pipeline applications for exercising multiplexed streams."""
import hashlib
import typing as ta

from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..types import IoPipelineMultiplexRefusal
from ..types import IoPipelineMultiplexStreamMetadata
from ..types import IoPipelineMultiplexStreamOpening


##


def payload(seed: ta.Any, size: int) -> bytes:
    out = bytearray()
    block = hashlib.sha256(repr(seed).encode()).digest()
    while len(out) < size:
        out.extend(block)
        block = hashlib.sha256(block).digest()
    return bytes(out[:size])


class Emit(IoPipelineMessages.AfterFinalInput):
    """Fed into a stream's pipeline to make its app emit messages."""

    def __init__(self, *msgs: ta.Any) -> None:
        super().__init__()

        self.msgs = msgs


class StreamApp(IoPipelineHandler):
    """
    A stream endpoint which records everything it receives. On InitialInput it sends `prelude` messages, then `send`
    (then `send_messages`), optionally followed by ShutdownOutput; on FinalInput it may send `respond` followed by
    ShutdownOutput, and closes with FinalOutput if `close_on_final_input`. In manual-read mode it requests input one
    batch at a time.
    """

    def __init__(
            self,
            *,
            prelude: ta.Sequence[ta.Any] = (),
            send: bytes = b'',
            send_messages: ta.Sequence[ta.Any] = (),
            shutdown_after_send: bool = False,
            respond: ta.Optional[bytes] = None,
            respond_messages: ta.Sequence[ta.Any] = (),
            echo: bool = False,
            manual_read: bool = False,
            close_on_final_input: bool = True,
            close_on: ta.Optional[ta.Callable[[ta.Any], bool]] = None,
            chunk_size: int = 4096,
    ) -> None:
        super().__init__()

        self._prelude = prelude
        self._send = send
        self._send_messages = send_messages
        self._shutdown_after_send = shutdown_after_send
        self._respond = respond
        self._respond_messages = respond_messages
        self._echo = echo
        self._manual_read = manual_read
        self._close_on_final_input = close_on_final_input
        self._close_on = close_on
        self._chunk_size = chunk_size

        self.received = bytearray()
        self.messages: ta.List[ta.Any] = []
        self.errors: ta.List[BaseException] = []
        self.writability: ta.List[ta.Any] = []
        self.flush_inputs = 0
        self.reads_requested = 0
        self.saw_initial_input = False
        self.saw_final_input = False
        self.metadata: ta.Optional[IoPipelineMultiplexStreamMetadata] = None

        self.shutdown_output = IoPipelineMessages.ShutdownOutput()
        self.final_output = IoPipelineMessages.FinalOutput()
        self.shutdown_sent = False
        self.final_sent = False

    def _read(self, ctx: IoPipelineHandlerContext) -> None:
        if self._manual_read and not self.saw_final_input:
            self.reads_requested += 1
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _send_all(self, ctx: IoPipelineHandlerContext, data: bytes, messages: ta.Sequence[ta.Any]) -> None:
        mv = memoryview(data)
        for pos in range(0, len(mv), self._chunk_size):
            ctx.feed_out(mv[pos:pos + self._chunk_size])
        for m in messages:
            ctx.feed_out(m)

    def shutdown(self, ctx: IoPipelineHandlerContext) -> None:
        if not self.shutdown_sent:
            self.shutdown_sent = True
            ctx.feed_out(self.shutdown_output)

    def close(self, ctx: IoPipelineHandlerContext) -> None:
        if not self.final_sent:
            self.final_sent = True
            ctx.feed_out(self.final_output)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, Emit):
            for m in msg.msgs:
                if m is IoPipelineMessages.ShutdownOutput:
                    self.shutdown(ctx)
                elif m is IoPipelineMessages.FinalOutput:
                    self.close(ctx)
                else:
                    ctx.feed_out(m)
            return

        if isinstance(msg, IoPipelineMessages.InitialInput):
            self.saw_initial_input = True
            self.metadata = ctx.pipeline.metadata.get(IoPipelineMultiplexStreamMetadata)
            ctx.feed_in(msg)
            for m in self._prelude:
                ctx.feed_out(m)
            if self._send or self._send_messages:
                self._send_all(ctx, self._send, self._send_messages)
            if self._shutdown_after_send:
                self.shutdown(ctx)
            self._read(ctx)
            return

        if ByteStreamBuffers.can_bytes(msg):
            data = ByteStreamBuffers.to_bytes(msg, strict=True)
            self.received.extend(data)
            if self._echo and not self.shutdown_sent:
                ctx.feed_out(data)
            return

        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self.flush_inputs += 1
            self._read(ctx)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            if self._respond is not None:
                self._send_all(ctx, self._respond, self._respond_messages)
                self.shutdown(ctx)
            if self._close_on_final_input:
                self.close(ctx)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return

        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.writability.append(type(msg))
            return

        self.messages.append(msg)
        if self._close_on is not None and self._close_on(msg):
            self.close(ctx)


class AppFactory:
    """A stream spec factory creating a `StreamApp` per stream, refusing any whose info matches `refuse`."""

    def __init__(
            self,
            make: ta.Callable[[IoPipelineMultiplexStreamOpening], StreamApp],
            *,
            refuse: ta.Optional[ta.Callable[[IoPipelineMultiplexStreamOpening], ta.Any]] = None,
            auto_read: ta.Union[bool, ta.Callable[[IoPipelineMultiplexStreamOpening], bool]] = True,
    ) -> None:
        super().__init__()

        self._make = make
        self._refuse = refuse
        self._auto_read = auto_read
        self.apps: ta.Dict[ta.Any, StreamApp] = {}
        self.openings: ta.List[IoPipelineMultiplexStreamOpening] = []

    def __call__(
            self,
            opening: IoPipelineMultiplexStreamOpening,
    ) -> ta.Union[IoPipeline.Spec, IoPipelineMultiplexRefusal]:
        self.openings.append(opening)
        if self._refuse is not None and (reason := self._refuse(opening)) is not None:
            return IoPipelineMultiplexRefusal(reason)
        app = self._make(opening)
        self.apps[opening.key] = app
        auto_read = self._auto_read if isinstance(self._auto_read, bool) else self._auto_read(opening)
        return app_spec(app, auto_read=auto_read)


def app_spec(app: IoPipelineHandler, *, auto_read: bool = True) -> IoPipeline.Spec:
    return IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=auto_read)])
