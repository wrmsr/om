# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Wire framing: bytes <-> RpcFrame.

The toolbox's own framing is a fixed-width unsigned length prefix, network order by default, followed by that many
payload bytes. Both directions enforce a maximum frame size; a received frame exceeding it is fatal, as the byte stream
cannot be resynchronized past it.

Written in the pipelines idiom as a `BufferedBytesToMessageDecoderIoPipelineHandler`, but kept in this package rather
than in `omcore.io.pipelines`: it is the rpc wire format, and lives with it for the foreseeable future.
"""
import dataclasses as dc
import typing as ta

from omcore.io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.streambufs.errors import FrameTooLargeByteStreamBufferError
from omcore.io.streambufs.errors import LimitByteStreamBufferError
from omcore.io.streambufs.framing import LengthFieldByteStreamFrameDecoder
from omcore.io.streambufs.types import ByteStreamBuffer
from omcore.io.streambufs.utils import ByteStreamBuffers

from .errors import RpcMessageTooLargeError
from .errors import RpcProtocolError


##


@dc.dataclass(frozen=True)
class RpcFrame:
    """One complete wire payload, before envelope decoding or after envelope encoding."""

    data: bytes


##


class RpcLengthPrefixedFramingIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    """
    bytes <-> RpcFrame with a length prefix of `length_field_length` bytes in `byteorder`.

    The limit applies to the payload, excluding the prefix. Outbound frames are sized by the envelope codec before they
    get here, so an oversized outbound frame is a programming error and raises.
    """

    def __init__(
            self,
            *,
            max_frame_bytes: int,
            length_field_length: int = 4,
            byteorder: ta.Literal['big', 'little'] = 'big',
            buffer_chunk_size: int = 64 * 1024,
    ) -> None:
        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)
        if length_field_length not in (1, 2, 4, 8):
            raise ValueError(length_field_length)
        if max_frame_bytes >= (1 << (8 * length_field_length)):
            raise ValueError(f'max_frame_bytes {max_frame_bytes} is not representable in {length_field_length} bytes')

        super().__init__(
            # The decoder checks frame sizes precisely itself; the buffer limit is a backstop bounding memory by what
            # one driver read batch can overshoot.
            max_buffer_size=None,
            buffer_chunk_size=buffer_chunk_size,
        )

        self._max_frame_bytes = max_frame_bytes
        self._length_field_length = length_field_length
        self._byteorder = byteorder

        self._fr = LengthFieldByteStreamFrameDecoder(
            length_field_length=length_field_length,
            byteorder=byteorder,
            initial_bytes_to_strip=length_field_length,
            max_frame_length=max_frame_bytes + length_field_length,
        )

    @property
    def max_frame_bytes(self) -> int:
        return self._max_frame_bytes

    #

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        try:
            frames = self._fr.decode(buf)
        except FrameTooLargeByteStreamBufferError as e:
            raise RpcMessageTooLargeError(f'received frame exceeds limit of {self._max_frame_bytes} bytes') from e
        except LimitByteStreamBufferError as e:
            raise RpcMessageTooLargeError(str(e)) from e
        except ValueError as e:
            raise RpcProtocolError(f'corrupt frame: {e}') from e

        for fr in frames:
            out.append(RpcFrame(ByteStreamBuffers.to_bytes(fr, strict=True)))

        if final and len(buf):
            # Raising during final input would strand FinalInput's propagation, so report the error as a message.
            buf.advance(len(buf))
            out.append(IoPipelineMessages.Error(
                RpcProtocolError('stream ended within a frame'),
                direction='inbound',
                handler=ctx.ref,
            ))

    def _encode_frame(self, frame: RpcFrame) -> bytes:
        return len(frame.data).to_bytes(self._length_field_length, self._byteorder) + frame.data

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcFrame):
            if len(msg.data) > self._max_frame_bytes:
                raise RpcMessageTooLargeError(
                    f'outbound frame is {len(msg.data)} bytes, exceeding limit {self._max_frame_bytes}',
                )

            msg = self._encode_frame(msg)

        ctx.feed_out(msg)
