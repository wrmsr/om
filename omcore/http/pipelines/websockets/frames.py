# ruff: noqa: UP006 UP007 UP045
# @om-lite
import os
import typing as ta

from ....io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.streambufs.direct import DirectByteStreamBufferView
from ....io.streambufs.types import ByteStreamBuffer
from ....io.streambufs.types import ByteStreamBufferView
from ....io.streambufs.utils import ByteStreamBuffers
from ....io.streambufs.utils import CanByteStreamBuffer
from ....lite.namespaces import NamespaceClass
from ..objects import IoPipelineHttpMessageBodyData
from ..requests import IoPipelineHttpRequestBodyData
from ..responses import IoPipelineHttpResponseBodyData
from .objects import IoPipelineWebsocketBinary
from .objects import IoPipelineWebsocketClose
from .objects import IoPipelineWebsocketFrame
from .objects import IoPipelineWebsocketOpcode
from .objects import IoPipelineWebsocketPing
from .objects import IoPipelineWebsocketPong
from .objects import IoPipelineWebsocketText


##


class IoPipelineWebsocketFrames(NamespaceClass):
    @staticmethod
    def mask_xor(data: bytes, key: bytes) -> bytes:
        if len(key) != 4:
            raise ValueError(key)

        n = len(data)
        if not n:
            return b''

        # XOR the whole payload as a single big int against the key cycled out to cover it - int.from_bytes / to_bytes
        # and big-int xor all run at C speed, roughly two orders of magnitude faster than a python-level per-byte loop.
        kb = key * ((n + 3) // 4)
        if len(kb) != n:
            kb = kb[:n]
        return (int.from_bytes(data, 'little') ^ int.from_bytes(kb, 'little')).to_bytes(n, 'little')


##


class IoPipelineWebsocketFrameEncoder(IoPipelineHandler):
    """Encodes WsFrame or high-level WsText/WsBinary/WsPing/WsPong/WsClose into bytes."""

    def __init__(self, *, mask: bool = False) -> None:
        super().__init__()

        self._mask = mask

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineWebsocketFrame):
            self._emit_frame(ctx, msg)
            return

        if isinstance(msg, IoPipelineWebsocketText):
            frame = IoPipelineWebsocketFrame(
                fin=True,
                opcode=IoPipelineWebsocketOpcode.TEXT,
                payload=msg.text.encode('utf-8'),
            )
            self._emit_frame(ctx, frame)
            return

        if isinstance(msg, IoPipelineWebsocketBinary):
            frame = IoPipelineWebsocketFrame(
                fin=True,
                opcode=IoPipelineWebsocketOpcode.BINARY,
                payload=msg.data,
            )
            self._emit_frame(ctx, frame)
            return

        if isinstance(msg, IoPipelineWebsocketPing):
            frame = IoPipelineWebsocketFrame(
                fin=True,
                opcode=IoPipelineWebsocketOpcode.PING,
                payload=msg.data,
            )
            self._emit_frame(ctx, frame)
            return

        if isinstance(msg, IoPipelineWebsocketPong):
            frame = IoPipelineWebsocketFrame(
                fin=True,
                opcode=IoPipelineWebsocketOpcode.PONG,
                payload=msg.data,
            )
            self._emit_frame(ctx, frame)
            return

        if isinstance(msg, IoPipelineWebsocketClose):
            payload = b''
            if msg.code or msg.reason:
                payload = msg.code.to_bytes(2, 'big')
                if msg.reason:
                    payload += msg.reason.encode('utf-8')
            frame = IoPipelineWebsocketFrame(
                fin=True,
                opcode=IoPipelineWebsocketOpcode.CLOSE,
                payload=payload,
            )
            self._emit_frame(ctx, frame)
            return

        ctx.feed_out(msg)

    def _emit_frame(self, ctx: IoPipelineHandlerContext, frame: IoPipelineWebsocketFrame) -> None:
        head, payload = self._encode_frame(frame, mask=self._mask)
        ctx.feed_out(head)
        if len(payload):
            ctx.feed_out(payload)

    def _encode_frame(
            self,
            frame: IoPipelineWebsocketFrame,
            *,
            mask: bool,
    ) -> ta.Tuple[ByteStreamBufferView, CanByteStreamBuffer]:
        b0 = (
            (0x80 if frame.fin else 0x00) |
            (0x40 if frame.rsv1 else 0) |
            (0x20 if frame.rsv2 else 0) |
            (0x10 if frame.rsv3 else 0) |
            (int(frame.opcode) & 0x0F)
        )
        payload = frame.payload
        ln = len(payload)

        h = bytearray()
        h.append(b0)

        mask_bit = 0x80 if mask else 0x00

        if ln < 126:
            h.append(mask_bit | ln)
        elif ln < (1 << 16):
            h.append(mask_bit | 126)
            h.extend(ln.to_bytes(2, 'big'))
        else:
            h.append(mask_bit | 127)
            h.extend(ln.to_bytes(8, 'big'))

        if mask:
            key = os.urandom(4)
            h.extend(key)
            payload = IoPipelineWebsocketFrames.mask_xor(
                ByteStreamBuffers.to_bytes(payload, strict=True),
                key,
            )

        return DirectByteStreamBufferView(bytes(h)), payload


class IoPipelineWebsocketClientFrameEncoder(IoPipelineWebsocketFrameEncoder):
    def __init__(self) -> None:
        super().__init__(mask=True)


class IoPipelineWebsocketServerFrameEncoder(IoPipelineWebsocketFrameEncoder):
    def __init__(self) -> None:
        super().__init__(mask=False)


##


_CONTROL_WEBSOCKET_OPCODES: ta.FrozenSet[IoPipelineWebsocketOpcode] = frozenset([
    IoPipelineWebsocketOpcode.CLOSE,
    IoPipelineWebsocketOpcode.PING,
    IoPipelineWebsocketOpcode.PONG,
])


class IoPipelineWebsocketFrameDecoder(BufferedBytesToMessageDecoderIoPipelineHandler):
    """
    Decodes inbound bytes into WsFrame objects. If expect_masked is True/False, validates the MASK bit accordingly; if
    None, accepts either.
    """

    DEFAULT_MAX_FRAME_SIZE: ta.ClassVar[int] = 16 * 1024 * 1024

    MAX_FRAME_HEADER_SIZE: ta.ClassVar[int] = 14  # 2 + 8 extended length + 4 mask key

    def __init__(
            self,
            *,
            expect_masked: bool,
            unwrap_message_body_cls: ta.Optional[ta.Type[IoPipelineHttpMessageBodyData]] = None,
            max_frame_size: ta.Optional[int] = DEFAULT_MAX_FRAME_SIZE,
            max_buffer_size: ta.Optional[int] = None,
    ) -> None:
        if max_frame_size is not None and max_frame_size < 1:
            raise ValueError(f'max_frame_size must be positive: {max_frame_size!r}')

        if max_buffer_size is None and max_frame_size is not None:
            # A frame is only parseable once fully buffered, so the buffer must be able to hold the largest accepted
            # frame plus its header.
            max_buffer_size = max_frame_size + self.MAX_FRAME_HEADER_SIZE

        super().__init__(max_buffer_size=max_buffer_size)

        self._expect_mask = expect_masked
        self._unwrap_message_body_cls = unwrap_message_body_cls
        self._max_frame_size = max_frame_size

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if (mbc := self._unwrap_message_body_cls) is not None and isinstance(msg, mbc):
            self._on_bytes_input(ctx, msg.data)
            return

        super().inbound(ctx, msg)

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while True:
            frm = self._try_parse_one(buf)
            if frm is None:
                return
            out.append(frm)

    def _try_parse_one(self, buf: ByteStreamBuffer) -> ta.Optional[IoPipelineWebsocketFrame]:
        if len(buf) < 2:
            return None

        head = buf.coalesce(2)
        b0 = head[0]
        b1 = head[1]

        fin = bool(b0 & 0x80)
        rsv1 = bool(b0 & 0x40)
        rsv2 = bool(b0 & 0x20)
        rsv3 = bool(b0 & 0x10)
        opcode = IoPipelineWebsocketOpcode(b0 & 0x0F)

        masked = bool(b1 & 0x80)
        ln = (b1 & 0x7F)
        o = 2

        if ln == 126:
            if len(buf) < o + 2:
                return None
            head = buf.coalesce(o + 2)
            ln = int.from_bytes(head[o:o + 2], 'big')
            o += 2
        elif ln == 127:
            if len(buf) < o + 8:
                return None
            head = buf.coalesce(o + 8)
            ln = int.from_bytes(head[o:o + 8], 'big')
            o += 8
            # RFC 6455 §5.2: 'the most significant bit MUST be 0'.
            if ln >> 63:
                raise ValueError('invalid websocket frame length')

        # Validate from the header, *before* buffering the payload - otherwise a frame claiming an absurd length simply
        # buffers the rest of the connection.
        if opcode in _CONTROL_WEBSOCKET_OPCODES and (not fin or ln > 125):
            raise ValueError('invalid control frame')

        if (mfs := self._max_frame_size) is not None and ln > mfs:
            raise ValueError(f'websocket frame length exceeds limit: {ln} > {mfs}')

        key = None
        if masked:
            if len(buf) < o + 4:
                return None
            head = buf.coalesce(o + 4)
            key = bytes(head[o:o + 4])
            o += 4

        if len(buf) < o + ln:
            return None

        buf.advance(o)
        payload: CanByteStreamBuffer = buf.split_to(ln)

        if self._expect_mask is True and not masked:
            raise ValueError('expected masked websocket frame')
        if self._expect_mask is False and masked:
            # We'll unmask but still consider it an error in strict mode; for now accept and unmask.
            pass

        if masked and key is not None:
            payload = DirectByteStreamBufferView(IoPipelineWebsocketFrames.mask_xor(
                ByteStreamBuffers.to_bytes(payload, strict=True),
                key,
            ))

        return IoPipelineWebsocketFrame(
            fin=fin,
            opcode=opcode,
            payload=payload,
            rsv1=rsv1,
            rsv2=rsv2,
            rsv3=rsv3,
        )


class IoPipelineWebsocketClientFrameDecoder(IoPipelineWebsocketFrameDecoder):
    def __init__(
            self,
            *,
            max_frame_size: ta.Optional[int] = IoPipelineWebsocketFrameDecoder.DEFAULT_MAX_FRAME_SIZE,
            max_buffer_size: ta.Optional[int] = None,
    ) -> None:
        super().__init__(
            expect_masked=False,
            unwrap_message_body_cls=IoPipelineHttpResponseBodyData,
            max_frame_size=max_frame_size,
            max_buffer_size=max_buffer_size,
        )


class IoPipelineWebsocketServerFrameDecoder(IoPipelineWebsocketFrameDecoder):
    def __init__(
            self,
            *,
            max_frame_size: ta.Optional[int] = IoPipelineWebsocketFrameDecoder.DEFAULT_MAX_FRAME_SIZE,
            max_buffer_size: ta.Optional[int] = None,
    ) -> None:
        super().__init__(
            expect_masked=True,
            unwrap_message_body_cls=IoPipelineHttpRequestBodyData,
            max_frame_size=max_frame_size,
            max_buffer_size=max_buffer_size,
        )
