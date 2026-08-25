"""
The protocol as omcore.io.pipelines handlers: a frontend message encoder, a backend message framer/decoder, and a
session handler which drives ProtocolSession operations. These are synchronous and transport-agnostic; sync and async
connections differ only in the pipeline driver they are attached to.
"""
import typing as ta

from ..... import check
from .....io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.errors import IncompleteDecodingIoPipelineError
from .....io.pipelines.errors import TimeoutIoPipelineError
from .....io.streambufs.types import ByteStreamBuffer
from .....sql.drivers.base.core.handlers import OperationDone
from .....sql.drivers.base.core.handlers import OperationRequest
from .....sql.drivers.base.core.handlers import OperationTimeoutsIoPipelineHandler
from ..errors import InterfaceError
from ..protocol import messages as msgs
from ..protocol.decoding import BackendMessageDecoder
from ..protocol.encoding import FrontendMessageEncoder
from ..protocol.packing import MESSAGE_HEADER
from ..protocol.packing import MESSAGE_HEADER_SIZE
from ..protocol.session import Operation
from ..protocol.session import ProtocolSession
from ..protocol.session import Step


##


class PgFrontendMessageEncoderIoPipelineHandler(IoPipelineHandler):
    def __init__(self, encoder: FrontendMessageEncoder) -> None:
        super().__init__()

        self._encoder = encoder

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, msgs.FrontendMessage):
            ctx.feed_out(self._encoder.encode(msg))
            return

        ctx.feed_out(msg)


class PgBackendMessageDecoderIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    def __init__(
            self,
            decoder: BackendMessageDecoder,
            *,
            max_buffer_size: int | None = None,
    ) -> None:
        super().__init__(max_buffer_size=max_buffer_size)

        self._decoder = decoder
        self._expect_ssl_response = False

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, msgs.SslRequest):
            # The reply to this is a single unframed byte rather than a message.
            self._expect_ssl_response = True

        ctx.feed_out(msg)

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: list[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while len(buf):
            if self._expect_ssl_response:
                self._expect_ssl_response = False
                out.append(msgs.SslResponse(accepted=buf.split_to(1).tobytes() == b'S'))
                continue

            if len(buf) < MESSAGE_HEADER_SIZE:
                break

            code, length = MESSAGE_HEADER.unpack(buf.coalesce(MESSAGE_HEADER_SIZE))
            payload_size = length - 4
            if len(buf) < MESSAGE_HEADER_SIZE + payload_size:
                break

            buf.advance(MESSAGE_HEADER_SIZE)
            payload = bytes(buf.split_to(payload_size).tobytes()) if payload_size else b''
            out.append(self._decoder.decode(code, payload))

        if final and len(buf):
            raise IncompleteDecodingIoPipelineError('incomplete backend message at end of input')


class PgSessionIoPipelineHandler(IoPipelineHandler):
    """
    Drives ProtocolSession operations: inbound OperationRequests start them, inbound backend messages advance them, and
    the frontend messages each Step calls for are fed outbound. An OperationDone is fed outbound when one finishes.
    """

    def __init__(self, session: ProtocolSession) -> None:
        super().__init__()

        self._session = session

    def _emit(self, ctx: IoPipelineHandlerContext, step: Step) -> None:
        while True:
            for msg in step.messages:
                ctx.feed_out(msg)
            if not step.more:
                break
            step = self._session.resume()

    def _fail_current(self, ctx: IoPipelineHandlerContext, exc: BaseException) -> None:
        op = self._session.current
        self._session.fail(exc)
        if op is not None:
            ctx.feed_out(OperationDone(op))

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OperationRequest):
            op = check.isinstance(msg.op, Operation)
            self._emit(ctx, op.start())
            if op.done:
                ctx.feed_out(OperationDone(op))
            return

        # Checked before frontend messages as a few message types, like CopyData, flow in both directions, and an
        # inbound one can only have come from the server.
        if isinstance(msg, msgs.BackendMessage):
            cur = self._session.current
            try:
                step = self._session.handle(msg)
            except Exception as e:
                self._fail_current(ctx, e)
                raise
            self._emit(ctx, step)
            if cur is not None and cur.done:
                ctx.feed_out(OperationDone(cur))
            return

        if isinstance(msg, msgs.FrontendMessage):
            # A bare outbound message enqueued by the connection, such as a Terminate.
            ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            exc = msg.exc
            if isinstance(exc, TimeoutIoPipelineError):
                new_exc = InterfaceError(str(exc))
                new_exc.__cause__ = exc
                exc = new_exc
            self._fail_current(ctx, exc)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._fail_current(ctx, InterfaceError('network error'))
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)


def make_pipeline_spec(
        session: ProtocolSession,
        *,
        read_timeout: float | None = None,
        write_timeout: float | None = None,
) -> IoPipeline.Spec:
    return IoPipeline.Spec([
        OperationTimeoutsIoPipelineHandler(
            read_timeout_s=read_timeout,
            write_timeout_s=write_timeout,
        ),
        PgFrontendMessageEncoderIoPipelineHandler(session.encoder),
        PgBackendMessageDecoderIoPipelineHandler(session.decoder),
        PgSessionIoPipelineHandler(session),
    ])
