# ruff: noqa: UP006 UP007 UP037 UP043 UP045
# @om-lite
"""
TODO:
 - chunked make_chunk_header - https://datatracker.ietf.org/doc/html/rfc9112#name-chunk-extensions
  - and make_body_data ...
 - fix exception handling lol - do we raise ValueError?? do we return aborted??
"""
import abc
import dataclasses as dc
import typing as ta
import weakref

from ...io.pipelines.bytes.buffering import InboundBytesBufferingIoPipelineHandler
from ...io.pipelines.bytes.decoders import BytesToMessageDecoderIoPipelineHandler
from ...io.pipelines.core import IoPipelineHandlerContext
from ...io.streambufs.scanning import ScanningByteStreamBuffer
from ...io.streambufs.segmented import SegmentedByteStreamBuffer
from ...io.streambufs.segmented import SegmentedByteStreamBufferView
from ...io.streambufs.types import MutableByteStreamBuffer
from ...io.streambufs.utils import ByteStreamBuffers
from ...io.streambufs.utils import CanByteStreamBuffer
from ...lite.abstract import Abstract
from ...lite.check import check
from ..headers import HttpHeaders
from ..parsing import HttpParseError
from ..parsing import HttpParser
from ..parsing import ParsedHttpTrailers
from ..parsing import parse_http_message
from ..parsing import parse_http_trailers
from .bodymodes import IoPipelineHttpBodyMode
from .bodymodes import IoPipelineHttpBodyModeError
from .objects import IoPipelineHttpMessageHead
from .objects import IoPipelineHttpMessageObjects


##


@dc.dataclass(frozen=True)
class IoPipelineHttpDecodingConfig:
    DEFAULT: ta.ClassVar['IoPipelineHttpDecodingConfig']

    parser_config: ta.Optional[HttpParser.Config] = None

    @dc.dataclass(frozen=True)
    class BufferConfig:
        max_size: ta.Optional[int]
        chunk_size: int

    head_buffer: BufferConfig = BufferConfig(max_size=4 * 1024, chunk_size=4 * 1024)

    max_chunk_size: ta.Optional[int] = None
    chunk_header_buffer: BufferConfig = BufferConfig(max_size=1024, chunk_size=1024)

    trailer_buffer: BufferConfig = BufferConfig(max_size=4 * 1024, chunk_size=4 * 1024)


IoPipelineHttpDecodingConfig.DEFAULT = IoPipelineHttpDecodingConfig()


#


_HTTP_CHUNK_SIZE_DIGITS: ta.FrozenSet[int] = frozenset(b'0123456789abcdefABCDEF')


#


class IoPipelineHttpObjectDecoder(
    IoPipelineHttpMessageObjects,
    InboundBytesBufferingIoPipelineHandler,
    BytesToMessageDecoderIoPipelineHandler,
    Abstract,
):
    def __init__(
            self,
            *,
            config: IoPipelineHttpDecodingConfig = IoPipelineHttpDecodingConfig.DEFAULT,
    ) -> None:
        super().__init__()

        self._config = config

        self._state: IoPipelineHttpObjectDecoder._State = self._HeadState(self)

    #

    def inbound_buffered_bytes(self) -> int:
        if (buf := self._state.buf) is None:
            return 0
        return len(buf)

    #

    @property
    @abc.abstractmethod
    def _parse_mode(self) -> HttpParser.Mode:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def _if_content_length_missing(self) -> ta.Literal['empty', 'eof']:
        raise NotImplementedError

    #

    def _select_body_mode(self, head: IoPipelineHttpMessageHead) -> IoPipelineHttpBodyMode:
        return IoPipelineHttpBodyMode.select(
            head.headers,
            if_length_missing=self._if_content_length_missing,
        )

    #

    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while True:
            if (ret := self._state.decode(ctx, data, out, final=final)) is None:
                return

            self._state, next_data = ret

            if next_data is None:
                return

            data = next_data

    #

    class _State(Abstract):
        def __init__(self, d: 'IoPipelineHttpObjectDecoder') -> None:
            super().__init__()

            self.__d_ref = weakref.ref(d)

        @property
        def _d(self) -> 'IoPipelineHttpObjectDecoder':
            return check.not_none(self.__d_ref())

        @property
        def buf(self) -> ta.Optional[MutableByteStreamBuffer]:
            return None

        def _abort(
                self,
                out: ta.List[ta.Any],
                reason: ta.Union[str, BaseException],
                data: ta.Optional[CanByteStreamBuffer] = None,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            out.append(self._d._make_aborted(reason))  # noqa
            return (self._d._AbortedState(self._d), data)  # noqa

        @abc.abstractmethod
        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            raise NotImplementedError

    #

    class _HeadState(_State):
        _buf: ta.Optional[MutableByteStreamBuffer] = None

        @property
        def buf(self) -> ta.Optional[MutableByteStreamBuffer]:
            return self._buf

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            if final:
                if (buf := self._buf) is not None and len(buf):
                    return self._abort(out, 'EOF before HTTP head complete')

                # A clean EOF with nothing buffered is not an error - it is just a peer which opened a connection and
                # sent nothing (or which closed cleanly between keepalive messages).
                return None

            done = False
            next_mvs: ta.List[memoryview]

            for mv in ByteStreamBuffers.iter_segments(data):
                if done:
                    next_mvs.append(mv)  # noqa
                    continue

                if (buf := self._buf) is None:
                    buf = self._buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(
                        max_size=self._d._config.head_buffer.max_size,  # noqa
                        chunk_size=self._d._config.head_buffer.chunk_size,  # noqa
                    ))

                rem_mv: ta.Optional[memoryview] = None

                if (max_buf := buf.max_size) is not None:
                    rem_buf = max_buf - len(buf)

                    if len(mv) > rem_buf:
                        buf.write(mv[:rem_buf])
                        rem_mv = mv[rem_buf:]
                    else:
                        buf.write(mv)

                else:
                    buf.write(mv)

                # Look for end of head
                i = buf.find(b'\r\n\r\n')
                if i < 0:
                    if rem_mv is not None:
                        return self._abort(out, 'Head exceeded max buffer size')

                    continue

                # Extract head
                head_view = buf.split_to(i + 4)

                # Parse and emit head
                raw = head_view.tobytes()
                try:
                    parsed = parse_http_message(
                        raw,
                        mode=self._d._parse_mode,  # noqa
                        config=self._d._config.parser_config,  # noqa
                    )
                except HttpParseError as e:
                    # Peer garbage is a normal, expected condition - it must abort the message, not raise out of the
                    # decoder (which would discard any messages already decoded from this same read).
                    return self._abort(out, e)

                head = self._d._make_head(parsed)  # noqa
                out.append(head)

                done = True
                next_mvs = []

                # Forward any remainder bytes (body bytes)
                if len(buf):
                    rem_view = buf.split_to(len(buf))
                    next_mvs.extend(rem_view.segments())

                if rem_mv is not None:
                    next_mvs.append(rem_mv)

            if done:
                return (
                    self._d._BodyModeState(self._d, head),  # noqa
                    SegmentedByteStreamBufferView.or_else(next_mvs, b''),
                )
            else:
                return None

    #

    class _BodyModeState(_State):
        def __init__(self, d: 'IoPipelineHttpObjectDecoder', head: IoPipelineHttpMessageHead) -> None:
            super().__init__(d)

            self._head = head

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            try:
                te = self._d._select_body_mode(self._head)  # noqa
            except IoPipelineHttpBodyModeError as e:
                return self._abort(out, f'Invalid Transfer-Encoding: {e.reason}')

            if te.mode == 'empty':
                out.append(self._d._make_end())  # noqa
                return (self._d._DoneState(self._d, self._head), data)  # noqa

            elif te.mode == 'eof':
                return (self._d._UntilEofContentState(self._d, self._head), data)  # noqa

            elif te.mode == 'cl':
                return (self._d._ContentLengthContentState(self._d, self._head, check.not_none(te.length)), data)  # noqa

            elif te.mode == 'chunked':
                return (self._d._HeaderChunkedContentState(self._d, self._head), data)  # noqa

            elif te.mode == 'tunnel':
                out.append(self._d._make_end())  # noqa
                return (self._d._TunnelState(self._d, self._head), data)  # noqa

            else:
                raise RuntimeError(f'unexpected mode {te!r}')

    #

    class _ContentState(_State, Abstract):
        def __init__(
                self,
                d: 'IoPipelineHttpObjectDecoder',
                head: IoPipelineHttpMessageHead,
        ) -> None:
            super().__init__(d)

            self._head = head

    #

    class _UntilEofContentState(_ContentState):
        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            body_mvs = [mv for mv in ByteStreamBuffers.iter_segments(data) if mv]
            if (body := SegmentedByteStreamBufferView.of_opt(body_mvs)) is not None:
                out.append(self._d._make_body_data(body))  # noqa

            if final:
                out.append(self._d._make_end())  # noqa
                return (self._d._DoneState(self._d, self._head), b'')  # noqa
            else:
                return None

    #

    class _TunnelState(_ContentState):
        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            if (body := SegmentedByteStreamBufferView.of_opt([
                    mv for mv in ByteStreamBuffers.iter_segments(data) if mv
            ])) is not None:
                out.append(body)

            return None

    #

    class _ContentLengthContentState(_ContentState):
        def __init__(
                self,
                d: 'IoPipelineHttpObjectDecoder',
                head: IoPipelineHttpMessageHead,
                content_length: int,
        ) -> None:
            check.arg(content_length > 0)

            super().__init__(d, head)

            self._remaining = content_length

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            body_mvs: ta.List[memoryview] = []
            next_mvs: ta.List[memoryview]
            ended = False

            for mv in ByteStreamBuffers.iter_segments(data):
                mvl = len(mv)
                if not mvl:
                    continue

                if self._remaining < 1:
                    next_mvs.append(mv)  # noqa
                    continue

                if self._remaining > mvl:
                    body_mvs.append(mv)
                    self._remaining -= mvl

                elif self._remaining == mvl:
                    body_mvs.append(mv)
                    self._remaining = 0
                    next_mvs = []
                    ended = True

                else:
                    body_mvs.append(mv[:self._remaining])
                    ofs = self._remaining
                    self._remaining = 0
                    next_mvs = [mv[ofs:]]
                    ended = True

            if (body := SegmentedByteStreamBufferView.of_opt(body_mvs)) is not None:
                out.append(self._d._make_body_data(body))  # noqa
            if ended:
                out.append(self._d._make_end())  # noqa

            if final and self._remaining > 0:
                return self._abort(out, 'EOF before HTTP body complete')
            elif self._remaining == 0:
                return (
                    self._d._DoneState(self._d, self._head),  # noqa
                    SegmentedByteStreamBufferView.or_else(next_mvs, b''),
                )
            else:
                return None

    #

    class _ChunkedContentState(_ContentState, Abstract):
        pass

    #

    class _HeaderChunkedContentState(_ChunkedContentState):
        _buf: ta.Optional[MutableByteStreamBuffer] = None

        @property
        def buf(self) -> ta.Optional[MutableByteStreamBuffer]:
            return self._buf

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            chunk_size: ta.Optional[int] = None
            next_mvs: ta.List[memoryview]

            for mv in ByteStreamBuffers.iter_segments(data):
                if chunk_size is not None:
                    next_mvs.append(mv)  # noqa
                    continue

                if (buf := self._buf) is None:
                    # TODO: Reuse a single chunk-header buffer across chunks - this currently allocates a fresh
                    #  ScanningByteStreamBuffer + SegmentedByteStreamBuffer per chunk header, which churns on
                    #  small-chunk streams.
                    buf = self._buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(
                        max_size=self._d._config.chunk_header_buffer.max_size,  # noqa
                        chunk_size=self._d._config.chunk_header_buffer.chunk_size,  # noqa
                    ))

                rem_mv: ta.Optional[memoryview] = None

                if (max_buf := buf.max_size) is not None:
                    rem_buf = max_buf - len(buf)

                    if len(mv) > rem_buf:
                        buf.write(mv[:rem_buf])
                        rem_mv = mv[rem_buf:]
                    else:
                        buf.write(mv)

                else:
                    buf.write(mv)

                # Parse chunk size line: <hex-size>[ chunk-ext ]\r\n
                i = buf.find(b'\r\n')
                if i < 0:
                    if rem_mv is not None:
                        return self._abort(out, 'Chunk header exceeded max buffer size')

                    continue

                size_line = buf.split_to(i + 2)

                size_bytes = size_line.tobytes()[:-2]  # Strip \r\n

                # Chunk extensions are ignored - https://datatracker.ietf.org/doc/html/rfc9112#name-chunk-extensions
                if (semi := size_bytes.find(b';')) >= 0:
                    size_bytes = size_bytes[:semi]

                # chunk-size is strictly 1*HEXDIG - int() would otherwise accept '0x5', '1_0', '+5', and even '-5'.
                if not size_bytes or not all(c in _HTTP_CHUNK_SIZE_DIGITS for c in size_bytes):
                    return self._abort(out, f'Invalid chunk size: {size_bytes!r}')

                chunk_size = int(size_bytes, 16)

                if (mcs := self._d._config.max_chunk_size) is not None and chunk_size > mcs:  # noqa
                    return self._abort(out, f'Content chunk size {chunk_size} exceeds maximum content chunk size: {mcs}')  # noqa

                next_mvs = []

                if len(buf) > 0:
                    next_mvs.extend(buf.segments())

                self._buf = None

                if rem_mv is not None:
                    next_mvs.append(rem_mv)

            if chunk_size is not None:
                if chunk_size == 0:
                    out.append(self._d._make_last_chunk())  # noqa
                    return (
                        self._d._TrailerChunkedContentState(self._d, self._head),  # noqa
                        SegmentedByteStreamBufferView.or_else(next_mvs, b''),
                    )
                else:
                    out.append(self._d._make_chunk(chunk_size))  # noqa
                    return (
                        self._d._DataChunkedContentState(self._d, self._head, chunk_size),  # noqa
                        SegmentedByteStreamBufferView.or_else(next_mvs, b''),
                    )
            elif final:
                return self._abort(out, 'EOF before HTTP chunk header complete')
            else:
                return None

    #

    class _DataChunkedContentState(_ChunkedContentState):
        def __init__(
                self,
                d: 'IoPipelineHttpObjectDecoder',
                head: IoPipelineHttpMessageHead,
                chunk_size: int,
        ) -> None:
            check.arg(chunk_size > 0)

            super().__init__(d, head)

            self._remaining = chunk_size

        _got_cr = False

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            body_mvs: ta.List[memoryview] = []
            next_mvs: ta.Optional[ta.List[memoryview]] = None

            for mv in ByteStreamBuffers.iter_segments(data):
                if next_mvs is not None:
                    next_mvs.append(mv)
                    continue

                mvl = len(mv)
                if mvl < 1:
                    continue

                if mvl < self._remaining:
                    self._remaining -= mvl
                    body_mvs.append(mv)
                    continue

                if self._remaining > 0:
                    if mvl == self._remaining:
                        body_mvs.append(mv)
                        self._remaining = 0
                        continue

                    body_mvs.append(mv[:self._remaining])
                    mv = mv[self._remaining:]
                    mvl = len(mv)
                    self._remaining = 0

                if mvl < 1:
                    continue

                if not self._got_cr:
                    if mv[0] != 0x0d:
                        if (body := SegmentedByteStreamBufferView.of_opt(body_mvs)) is not None:
                            out.append(self._d._make_body_data(body))  # noqa
                        return self._abort(out, f'Expected \\r\\n after chunk data, got {bytes([mv[0]])!r}')
                    self._got_cr = True
                    mv = mv[1:]
                    mvl -= 1
                    if mvl < 1:
                        continue

                if mv[0] != 0x0a:
                    if (body := SegmentedByteStreamBufferView.of_opt(body_mvs)) is not None:
                        out.append(self._d._make_body_data(body))  # noqa
                    return self._abort(out, f'Expected \\r\\n after chunk data, got {bytes([mv[0]])!r}')
                mv = mv[1:]
                mvl -= 1

                next_mvs = []

                if mvl > 0:
                    next_mvs.append(mv)

            if (body := SegmentedByteStreamBufferView.of_opt(body_mvs)) is not None:
                out.append(self._d._make_body_data(body))  # noqa

            if next_mvs is not None:
                out.append(self._d._make_end_chunk())  # noqa
                return (
                    self._d._HeaderChunkedContentState(self._d, self._head),  # noqa
                    SegmentedByteStreamBufferView.or_else(next_mvs, b''),
                )
            elif final:
                return self._abort(out, 'EOF before HTTP chunk complete')
            else:
                return None

    #

    class _TrailerChunkedContentState(_ChunkedContentState):
        """
        Consumes the trailer section following the last chunk.

        The section is either a bare CRLF or one or more field-lines terminated by an empty line. Parsed fields are
        carried on the emitted ChunkedTrailers message, kept separate from the head's headers - RFC 9110 §6.5.1 only
        permits merging them for fields a recipient understands.
        """

        _buf: ta.Optional[MutableByteStreamBuffer] = None

        @property
        def buf(self) -> ta.Optional[MutableByteStreamBuffer]:
            return self._buf

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            done = False
            next_mvs: ta.List[memoryview]

            for mv in ByteStreamBuffers.iter_segments(data):
                if done:
                    next_mvs.append(mv)  # noqa
                    continue

                if (buf := self._buf) is None:
                    buf = self._buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(
                        max_size=self._d._config.trailer_buffer.max_size,  # noqa
                        chunk_size=self._d._config.trailer_buffer.chunk_size,  # noqa
                    ))

                rem_mv: ta.Optional[memoryview] = None

                if (max_buf := buf.max_size) is not None:
                    rem_buf = max_buf - len(buf)

                    if len(mv) > rem_buf:
                        buf.write(mv[:rem_buf])
                        rem_mv = mv[rem_buf:]
                    else:
                        buf.write(mv)

                else:
                    buf.write(mv)

                # An empty trailer section is just the terminating CRLF, otherwise it ends with an empty line.
                if buf.find(b'\r\n') == 0:
                    end = 2
                else:
                    i = buf.find(b'\r\n\r\n')
                    if i < 0:
                        if rem_mv is not None:
                            return self._abort(out, 'Trailers exceeded max buffer size')

                        continue

                    end = i + 4

                trailer_view = buf.split_to(end)

                parsed_trailers: ta.Optional[ParsedHttpTrailers] = None
                if end > 2:
                    try:
                        parsed_trailers = parse_http_trailers(
                            trailer_view.tobytes(),
                            config=self._d._config.parser_config,  # noqa
                        )
                    except HttpParseError as e:
                        return self._abort(out, e)

                self._buf = None

                out.append(self._d._make_chunked_trailers(  # noqa
                    HttpHeaders(parsed_trailers.headers.entries) if parsed_trailers is not None else None,
                    parsed_trailers,
                ))
                out.append(self._d._make_end())  # noqa

                done = True
                next_mvs = []

                if len(buf):
                    next_mvs.extend(buf.split_to(len(buf)).segments())

                if rem_mv is not None:
                    next_mvs.append(rem_mv)

            if done:
                return (
                    self._d._DoneState(self._d, self._head),  # noqa
                    SegmentedByteStreamBufferView.or_else(next_mvs, b''),
                )
            elif final:
                return self._abort(out, 'EOF before HTTP trailer complete')
            else:
                return None

    #

    class _DoneState(_State):
        def __init__(
                self,
                d: 'IoPipelineHttpObjectDecoder',
                head: ta.Optional[IoPipelineHttpMessageHead] = None,
        ) -> None:
            super().__init__(d)

            self._head = head

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            if not len(data):
                return None

            return (self._d._HeadState(self._d), data)  # noqa

    #

    class _AbortedState(_State):
        """
        Terminal state - all further input is discarded.

        Aborts are a normal consequence of peer garbage, and further input is guaranteed: the peer's remaining bytes are
        already in flight, and the transport is torn down out of band.
        """

        def decode(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> ta.Optional[ta.Tuple['IoPipelineHttpObjectDecoder._State', ta.Optional[CanByteStreamBuffer]]]:
            return None
