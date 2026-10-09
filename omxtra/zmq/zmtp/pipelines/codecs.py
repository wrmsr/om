"""
The ZMTP wire codec: bytes to and from greetings, commands, and whole multipart messages.

Inbound it emits the peer's greeting, each command, and each complete message - never a partial one - so the base
decoder's read requests already cover frames which do not yet complete anything. A protocol violation is emitted inbound
as an Error in order after whatever was completed before it, and everything after it is discarded.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore.io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.streambufs.types import ByteStreamBuffer

from ...api.messages import DEFAULT_MESSAGE_LIMITS
from ...api.messages import MessageLimits
from ..commands import ZmtpCommand
from ..commands import decode_command_body
from ..errors import ZmtpLimitError
from ..errors import ZmtpProtocolError
from ..errors import ZmtpTruncatedError
from ..frames import FLAG_COMMAND
from ..frames import FLAG_LONG
from ..frames import FLAG_MORE
from ..frames import LONG_HEADER_SIZE
from ..frames import RESERVED_FLAGS
from ..frames import SHORT_HEADER_SIZE
from ..frames import encode_command_frame
from ..frames import encode_message
from ..greetings import GREETING_SIZE
from ..greetings import ZmtpGreeting
from ..greetings import check_greeting_prefix
from ..greetings import decode_greeting
from ..greetings import encode_greeting
from .messages import ZmtpMessage


##


@dc.dataclass(frozen=True)
class ZmtpCodecConfig:
    limits: MessageLimits = DEFAULT_MESSAGE_LIMITS
    max_command_size: int = 64 * 1024

    def __post_init__(self) -> None:
        if self.max_command_size < 1:
            raise ValueError(self.max_command_size)


class ZmtpCodecIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    def __init__(self, config: ZmtpCodecConfig | None = None) -> None:
        super().__init__()

        if config is None:
            config = ZmtpCodecConfig()
        self._config = config

        self._greeted = False
        self._failed = False

        # The current frame, once its header has been read.
        self._frame_flags: int | None = None
        self._frame_size = 0

        # The current multipart message's completed frames.
        self._parts: list[bytes] = []
        self._parts_size = 0

    #

    def _read_header(self, buf: ByteStreamBuffer) -> bool:
        if len(buf) < SHORT_HEADER_SIZE:
            return False

        flags = buf.coalesce(1)[0]
        if flags & RESERVED_FLAGS:
            raise ZmtpProtocolError(f'reserved frame flags set: {flags:#04x}')
        is_command = bool(flags & FLAG_COMMAND)
        if is_command and flags & FLAG_MORE:
            raise ZmtpProtocolError('command frame with MORE')
        if is_command and self._parts:
            raise ZmtpProtocolError('command frame inside a multipart message')

        if flags & FLAG_LONG:
            if len(buf) < LONG_HEADER_SIZE:
                return False
            size = int.from_bytes(buf.coalesce(LONG_HEADER_SIZE)[1:LONG_HEADER_SIZE], 'big')
            header_size = LONG_HEADER_SIZE
        else:
            size = buf.coalesce(SHORT_HEADER_SIZE)[1]
            header_size = SHORT_HEADER_SIZE

        # Bounds are checked from the header alone, before any of the body is buffered.
        limits = self._config.limits
        if is_command:
            if size > self._config.max_command_size:
                raise ZmtpLimitError(f'command frame of {size} bytes exceeds {self._config.max_command_size}')
        else:
            if size > limits.max_frame_size:
                raise ZmtpLimitError(f'frame of {size} bytes exceeds {limits.max_frame_size}')
            if len(self._parts) + 1 > limits.max_frames:
                raise ZmtpLimitError(f'message exceeds {limits.max_frames} frames')
            if self._parts_size + size > limits.max_message_size:
                raise ZmtpLimitError(f'message exceeds {limits.max_message_size} bytes')

        buf.advance(header_size)
        self._frame_flags = flags
        self._frame_size = size
        return True

    def _read_frame(self, buf: ByteStreamBuffer, out: list[ta.Any]) -> bool:
        if self._frame_flags is None and not self._read_header(buf):
            return False

        size = self._frame_size
        if len(buf) < size:
            return False

        flags = self._frame_flags
        self._frame_flags = None
        body = bytes(buf.split_to(size)) if size else b''

        if flags & FLAG_COMMAND:  # type: ignore[operator]
            out.append(decode_command_body(body))

        else:
            self._parts.append(body)
            self._parts_size += size
            if not (flags & FLAG_MORE):  # type: ignore[operator]
                out.append(ZmtpMessage(tuple(self._parts)))
                self._parts = []
                self._parts_size = 0

        return True

    def _decode_frames(self, buf: ByteStreamBuffer, out: list[ta.Any]) -> None:
        if not self._greeted:
            check_greeting_prefix(buf.coalesce(min(len(buf), GREETING_SIZE)))
            if len(buf) < GREETING_SIZE:
                return
            out.append(decode_greeting(bytes(buf.split_to(GREETING_SIZE))))
            self._greeted = True

        while self._read_frame(buf, out):
            pass

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: list[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        if self._failed:
            buf.advance(len(buf))
            return

        try:
            if len(buf):
                self._decode_frames(buf, out)

            if final and (len(buf) or self._parts or self._frame_flags is not None):
                raise ZmtpTruncatedError('connection ended inside a greeting, frame, or message')

        except ZmtpProtocolError as e:
            self._failed = True
            buf.advance(len(buf))
            out.append(IoPipelineMessages.Error(e, direction='inbound', handler=ctx.ref))

    #

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, ZmtpMessage):
            for piece in encode_message(msg.frames):
                ctx.feed_out(piece)

        elif isinstance(msg, ZmtpCommand):
            ctx.feed_out(encode_command_frame(msg.name, msg.data))

        elif isinstance(msg, ZmtpGreeting):
            ctx.feed_out(encode_greeting(msg))

        else:
            ctx.feed_out(msg)
