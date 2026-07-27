# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta

from ...io.pipelines.bytes.buffering import OutboundBytesBufferingIoPipelineHandler
from ...io.pipelines.core import IoPipelineHandler
from ...io.pipelines.core import IoPipelineHandlerContext
from ...io.pipelines.core import IoPipelineMessages
from ...io.pipelines.flow.types import IoPipelineFlow
from ...io.pipelines.flow.types import IoPipelineFlowMessages
from ...io.pipelines.handlers.decoders import MessageToMessageDecoderIoPipelineHandler
from ...lite.abstract import Abstract
from ...lite.bytes import BytesLike
from .objects import IoPipelineHttpMessageObjects


##


class IoPipelineHttpObjectChunker(
    IoPipelineHttpMessageObjects,
    OutboundBytesBufferingIoPipelineHandler,
    IoPipelineHandler,
    Abstract,
):
    """
    Outbound handler that wraps BodyData messages in chunked transfer encoding framing (Chunk, EndChunk, LastChunk,
    ChunkedTrailers).

    Buffers outbound BodyData and flushes on FlushOutput, End, or when the buffer reaches an optional max_chunk_size.
    Sits between the Compressor and Encoder so that chunk sizes reflect compressed data sizes.

    Its buffered byte count participates in output writability: the local high/low watermark state is combined with the
    downstream transport state and only effective transitions are announced upstream.
    """

    def __init__(
            self,
            *,
            max_chunk_size: ta.Optional[int] = None,
            write_high_watermark: int = 64 * 1024,
            write_low_watermark: int = 16 * 1024,
    ) -> None:
        super().__init__()

        if not 0 <= write_low_watermark <= write_high_watermark:
            raise ValueError((write_low_watermark, write_high_watermark))

        self._max_chunk_size = max_chunk_size
        self._write_high_watermark = write_high_watermark
        self._write_low_watermark = write_low_watermark

        self._active = False
        self._buf: ta.List[BytesLike] = []
        self._buf_size = 0

        self._downstream_writable = True
        self._self_writable = True
        self._announced_writable = True
        self._outbound_depth = 0

    #

    def _reset(self) -> None:
        self._active = False
        self._buf.clear()
        self._buf_size = 0

    def outbound_buffered_bytes(self) -> int:
        return self._buf_size

    #

    def _update_writability(self, ctx: IoPipelineHandlerContext) -> None:
        if self._self_writable:
            if self._buf_size > self._write_high_watermark:
                self._self_writable = False

        elif self._buf_size <= self._write_low_watermark:
            self._self_writable = True

        if self._outbound_depth or ctx.services.find(IoPipelineFlow) is None:
            return

        effective = self._downstream_writable and self._self_writable
        if effective != self._announced_writable:
            self._announced_writable = effective
            ctx.feed_in(
                IoPipelineFlowMessages.ReadyForOutput() if effective
                else IoPipelineFlowMessages.PauseOutput(),
            )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._downstream_writable = True
            self._update_writability(ctx)

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._downstream_writable = False
            self._update_writability(ctx)

        else:
            ctx.feed_in(msg)

    #

    def _flush_buf(self, ctx: IoPipelineHandlerContext) -> None:
        if self._buf_size < 1:
            return

        size = self._buf_size
        buf = self._buf
        self._buf = []
        self._buf_size = 0

        ctx.feed_out(self._make_chunk(size))
        for data in buf:
            ctx.feed_out(self._make_body_data(data))
        ctx.feed_out(self._make_end_chunk())

    def _buffer_data(self, ctx: IoPipelineHandlerContext, data: BytesLike) -> None:
        dl = len(data)

        if (mcs := self._max_chunk_size) is not None and (self._buf_size + dl) > mcs:
            self._flush_buf(ctx)

        self._buf.append(data)
        self._buf_size += dl

        if mcs is not None and dl >= mcs:
            self._flush_buf(ctx)

    #

    def _outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, self._head_type):
            self._active = msg.headers.contains_value('transfer-encoding', 'chunked', ignore_case=True)
            ctx.feed_out(msg)
            return

        if isinstance(msg, self._full_type):
            if msg.head.headers.contains_value('transfer-encoding', 'chunked', ignore_case=True):
                ctx.feed_out(msg.head)

                if len(msg.body) > 0:
                    self._buffer_data(ctx, msg.body)

                self._flush_buf(ctx)
                ctx.feed_out(self._make_last_chunk())
                ctx.feed_out(self._make_chunked_trailers())
                ctx.feed_out(self._make_end())
                return

            ctx.feed_out(msg)
            return

        if self._active:
            if isinstance(msg, self._body_data_type):
                self._buffer_data(ctx, msg.data)
                return

            if isinstance(msg, IoPipelineFlowMessages.FlushOutput):
                self._flush_buf(ctx)
                ctx.feed_out(msg)
                return

            if isinstance(msg, self._end_type):
                self._flush_buf(ctx)
                ctx.feed_out(self._make_last_chunk())
                ctx.feed_out(self._make_chunked_trailers())
                self._reset()
                ctx.feed_out(msg)
                return

            if isinstance(msg, self._aborted_type):
                self._reset()
                ctx.feed_out(msg)
                return

            if isinstance(msg, IoPipelineMessages.FinalOutput):
                self._reset()
                ctx.feed_out(self._make_aborted('eof before end of message'))
                ctx.feed_out(msg)
                return

        ctx.feed_out(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self._outbound_depth += 1
        try:
            self._outbound(ctx, msg)
        finally:
            self._outbound_depth -= 1
            if not self._outbound_depth:
                self._update_writability(ctx)


##


class IoPipelineHttpObjectDechunker(
    IoPipelineHttpMessageObjects,
    MessageToMessageDecoderIoPipelineHandler,
    Abstract,
):
    """
    Inbound handler that strips chunked transfer encoding framing messages (Chunk, EndChunk, LastChunk,
    ChunkedTrailers), leaving only Head + BodyData* + End for downstream handlers.

    Sits between the Decoder and Decompressor in the pipeline so that the decompressor sees only content-level messages
    without stale chunk sizes.
    """

    def __init__(self) -> None:
        super().__init__()

        self._active = False

    def _should_decode(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> bool:
        return isinstance(msg, (
            self._head_type,
            self._chunk_type,
            self._end_chunk_type,
            self._last_chunk_type,
            self._chunked_trailers_type,
            self._body_data_type,
            self._end_type,
            self._aborted_type,
        ))

    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            msg: ta.Any,
            out: ta.List[ta.Any],
    ) -> None:
        if isinstance(msg, self._head_type):
            self._active = msg.headers.contains_value('transfer-encoding', 'chunked', ignore_case=True)
            out.append(msg)
            return

        if self._active and isinstance(msg, (
                self._chunk_type,
                self._end_chunk_type,
                self._last_chunk_type,
                self._chunked_trailers_type,
        )):
            return

        if isinstance(msg, (self._end_type, self._aborted_type)):
            self._active = False

        out.append(msg)
