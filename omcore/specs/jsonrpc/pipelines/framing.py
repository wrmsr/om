"""
Wire framing: bytes <-> JsonrpcFrame.

Two dialects are in use: newline-delimited JSON (MCP and ACP over stdio and sockets) and LSP-style
`Content-Length` headers. Both decoders enforce a maximum frame size; a received frame exceeding it is fatal, as the
byte stream cannot be resynchronized past it, and is raised as JsonrpcMessageTooLargeError which the pipeline delivers
to the session as an Error.
"""
import abc
import typing as ta

from .... import dataclasses as dc
from .... import lang
from ....io.pipelines import all as ipl
from ....io.streambufs import all as isb
from ..errors import JsonrpcMessageTooLargeError
from ..errors import JsonrpcProtocolError


##


@dc.dataclass(frozen=True)
class JsonrpcFrame(lang.Final):
    """One complete wire payload, before JSON decoding or after JSON encoding."""

    data: bytes


##


class JsonrpcFramingHandler(ipl.BufferedBytesToMessageDecoderHandler, lang.Abstract):
    def __init__(
            self,
            *,
            max_frame_bytes: int,
            buffer_chunk_size: int = 64 * 1024,
    ) -> None:
        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)

        super().__init__(
            # The decoders check frame sizes precisely themselves; the buffer limit is a backstop bounding memory by
            # what one driver read batch can overshoot.
            max_buffer_size=None,
            buffer_chunk_size=buffer_chunk_size,
            scanning_buffer=True,
        )

        self._max_frame_bytes = max_frame_bytes

    @property
    def max_frame_bytes(self) -> int:
        return self._max_frame_bytes

    #

    @abc.abstractmethod
    def _encode_frame(self, frame: JsonrpcFrame) -> bytes:
        raise NotImplementedError

    def outbound(self, ctx: ipl.HandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, JsonrpcFrame):
            # The codec sizes outbound frames before they get here; a raw oversized frame is a programming error.
            if len(msg.data) > self._max_frame_bytes:
                raise JsonrpcMessageTooLargeError(
                    f'outbound frame is {len(msg.data)} bytes, exceeding limit {self._max_frame_bytes}',
                )

            msg = self._encode_frame(msg)

        ctx.feed_out(msg)


##


class NdjsonJsonrpcFramingHandler(JsonrpcFramingHandler):
    """
    Newline-delimited JSON: one payload per line. Trailing carriage returns are tolerated and blank lines are skipped.

    Compact JSON never contains a raw newline, so encoding is just appending one.
    """

    def __init__(
            self,
            *,
            max_frame_bytes: int,
            buffer_chunk_size: int = 64 * 1024,
    ) -> None:
        super().__init__(
            max_frame_bytes=max_frame_bytes,
            buffer_chunk_size=buffer_chunk_size,
        )

        # The delimiter is not counted against the frame size, so allow it on top.
        self._fr = isb.LongestMatchDelimiterFrameDecoder(
            [b'\n'],
            keep_ends=False,
            max_size=max_frame_bytes + 1,
        )

    def _decode_buffer(
            self,
            ctx: ipl.HandlerContext,
            buf: isb.Buffer,
            out: list[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        try:
            lines = self._fr.decode(buf, final=final)
        except isb.LimitBufferError as e:
            raise JsonrpcMessageTooLargeError(
                f'received line exceeds limit of {self._max_frame_bytes} bytes',
            ) from e

        if final and len(buf):
            # Be liberal: some peers omit the final newline before closing. The line is decoded like any other, and if
            # it is truncated garbage the codec answers it as a parse error like any other.
            if len(buf) > self._max_frame_bytes:
                # Raising during final input would strand FinalInput's propagation, so report the error as a message.
                buf.advance(len(buf))
                out.append(ipl.Messages.Error(
                    JsonrpcMessageTooLargeError(f'received line exceeds limit of {self._max_frame_bytes} bytes'),
                    direction='inbound',
                    handler=ctx.ref,
                ))
                return
            lines.append(buf.split_to(len(buf)))

        for line in lines:
            data = isb.Buffers.to_bytes(line, strict=True)
            if data.endswith(b'\r'):
                data = data[:-1]
            if not data.strip():
                continue
            if len(data) > self._max_frame_bytes:
                raise JsonrpcMessageTooLargeError(
                    f'received line is {len(data)} bytes, exceeding limit {self._max_frame_bytes}',
                )
            out.append(JsonrpcFrame(data))

    def _encode_frame(self, frame: JsonrpcFrame) -> bytes:
        return frame.data + b'\n'


##


class ContentLengthJsonrpcFramingHandler(JsonrpcFramingHandler):
    """
    LSP-style framing: a block of `Name: value` header lines terminated by a blank line, then exactly `Content-Length`
    bytes of payload. Only `Content-Length` is interpreted; any other header, notably `Content-Type`, is ignored. Lines
    end in `\\r\\n` per the LSP spec, though a bare `\\n` is tolerated on receipt.
    """

    _CONTENT_LENGTH_HEADER: ta.ClassVar[bytes] = b'content-length'

    def __init__(
            self,
            *,
            max_frame_bytes: int,
            max_header_bytes: int = 8 * 1024,
            buffer_chunk_size: int = 64 * 1024,
    ) -> None:
        super().__init__(
            max_frame_bytes=max_frame_bytes,
            buffer_chunk_size=buffer_chunk_size,
        )

        if max_header_bytes < 1:
            raise ValueError(max_header_bytes)
        self._max_header_bytes = max_header_bytes

        # Per-frame decode state: the content length once its headers have been fully read.
        self._content_length: int | None = None
        self._header_bytes = 0

    def _parse_header_line(self, line: bytes) -> None:
        name, sep, value = line.partition(b':')
        if not sep:
            raise JsonrpcProtocolError(f'malformed header line: {line!r}')

        if name.strip().lower() != self._CONTENT_LENGTH_HEADER:
            return

        if self._content_length is not None:
            raise JsonrpcProtocolError('duplicate Content-Length header')

        try:
            n = int(value.strip())
        except ValueError:
            raise JsonrpcProtocolError(f'malformed Content-Length header: {value!r}') from None
        if n < 0:
            raise JsonrpcProtocolError(f'negative Content-Length: {n}')
        if n > self._max_frame_bytes:
            raise JsonrpcMessageTooLargeError(
                f'received Content-Length of {n} bytes exceeds limit {self._max_frame_bytes}',
            )

        self._content_length = n

    # Distinguishes 'still reading headers' from 'headers done, reading body' since a body may legitimately be zero
    # bytes long.
    _headers_done = False

    def _decode_buffer(
            self,
            ctx: ipl.HandlerContext,
            buf: isb.Buffer,
            out: list[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while True:
            if not self._headers_done:
                i = buf.find(b'\n')
                if i < 0:
                    if len(buf) > self._max_header_bytes:
                        raise JsonrpcProtocolError(
                            f'header block exceeds limit of {self._max_header_bytes} bytes',
                        )
                    break

                line = isb.Buffers.to_bytes(buf.split_to(i + 1), strict=True)
                self._header_bytes += len(line)
                if self._header_bytes > self._max_header_bytes:
                    raise JsonrpcProtocolError(
                        f'header block exceeds limit of {self._max_header_bytes} bytes',
                    )

                line = line.rstrip(b'\r\n')
                if line:
                    self._parse_header_line(line)
                    continue

                if self._content_length is None:
                    raise JsonrpcProtocolError('missing Content-Length header')

                self._headers_done = True
                # Fall through to body reading.

            n = ta.cast(int, self._content_length)
            if len(buf) < n:
                break

            out.append(JsonrpcFrame(isb.Buffers.to_bytes(buf.split_to(n), strict=True)))

            self._headers_done = False
            self._content_length = None
            self._header_bytes = 0

        if final and (len(buf) or self._headers_done):
            # Raising during final input would strand FinalInput's propagation, so report the error as a message.
            buf.advance(len(buf))
            self._headers_done = False
            self._content_length = None
            self._header_bytes = 0
            out.append(ipl.Messages.Error(
                JsonrpcProtocolError('stream ended within a frame'),
                direction='inbound',
                handler=ctx.ref,
            ))

    def _encode_frame(self, frame: JsonrpcFrame) -> bytes:
        return b''.join([
            b'Content-Length: ',
            str(len(frame.data)).encode('ascii'),
            b'\r\n\r\n',
            frame.data,
        ])
