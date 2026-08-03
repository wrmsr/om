# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta

from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.streambufs.utils import ByteStreamBuffers
from .objects import IoPipelineWebsocketBinary
from .objects import IoPipelineWebsocketClose
from .objects import IoPipelineWebsocketFrame
from .objects import IoPipelineWebsocketOpcode
from .objects import IoPipelineWebsocketPing
from .objects import IoPipelineWebsocketPong
from .objects import IoPipelineWebsocketText


##


class IoPipelineWebsocketAggregator(IoPipelineHandler):
    """
    Aggregates fragmented data frames into WsText/WsBinary messages. Control frames (PING/PONG/CLOSE) are forwarded as
    WsPing/WsPong/WsClose events.
    """

    _assembling: ta.Optional[ta.Tuple[IoPipelineWebsocketOpcode, bytearray]] = None

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if not isinstance(msg, IoPipelineWebsocketFrame):
            ctx.feed_in(msg)
            return

        op = msg.opcode

        if op == IoPipelineWebsocketOpcode.TEXT or op == IoPipelineWebsocketOpcode.BINARY:
            if self._assembling is not None:
                # RFC 6455 §5.4: data frames may not be interleaved with an in-progress fragmented message. Drop the
                # partial message before failing so a later continuation cannot be appended to it.
                self._assembling = None
                raise ValueError('unexpected websocket data frame during fragmented message')

            if msg.fin:
                if op == IoPipelineWebsocketOpcode.TEXT:
                    ctx.feed_in(IoPipelineWebsocketText(
                        ByteStreamBuffers.to_bytes(msg.payload, strict=True).decode('utf-8'),
                    ))
                else:
                    ctx.feed_in(IoPipelineWebsocketBinary(msg.payload))
                return

            self._assembling = (op, bytearray(ByteStreamBuffers.to_bytes(msg.payload, strict=True)))
            return

        if op == IoPipelineWebsocketOpcode.CONTINUATION:
            if self._assembling is None:
                raise ValueError('unexpected websocket continuation frame')

            first_op, buf = self._assembling
            for mv in ByteStreamBuffers.iter_segments(msg.payload):
                buf.extend(mv)

            if msg.fin:
                data = bytes(buf)
                self._assembling = None
                if first_op == IoPipelineWebsocketOpcode.TEXT:
                    ctx.feed_in(IoPipelineWebsocketText(data.decode('utf-8')))
                else:
                    ctx.feed_in(IoPipelineWebsocketBinary(data))
            return

        if op == IoPipelineWebsocketOpcode.PING:
            ctx.feed_in(IoPipelineWebsocketPing(msg.payload))
            return

        if op == IoPipelineWebsocketOpcode.PONG:
            ctx.feed_in(IoPipelineWebsocketPong(msg.payload))
            return

        if op == IoPipelineWebsocketOpcode.CLOSE:
            payload = ByteStreamBuffers.to_bytes(msg.payload, strict=True)
            code = 1000
            reason = ''
            if len(payload) >= 2:
                code = int.from_bytes(payload[:2], 'big')
                if len(payload) > 2:
                    try:
                        reason = payload[2:].decode('utf-8')
                    except UnicodeDecodeError:
                        reason = ''
            ctx.feed_in(IoPipelineWebsocketClose(code=code, reason=reason))
            return

        # Unknown/reserved opcodes: pass through
        ctx.feed_in(msg)  # type: ignore[unreachable]
