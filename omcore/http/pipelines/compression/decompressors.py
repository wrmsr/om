# ruff: noqa: UP006 UP037 UP045
# @om-lite
import collections
import dataclasses as dc
import typing as ta

from ....io.pipelines.bytes.buffering import InboundBytesBufferingIoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.flow.types import IoPipelineFlow
from ....io.pipelines.flow.types import IoPipelineFlowMessages
from ....io.streambufs.direct import DirectByteStreamBufferView
from ....io.streambufs.utils import ByteStreamBuffers
from ....lite.abstract import Abstract
from ....lite.bytes import BytesLike
from ..objects import IoPipelineHttpMessageBodyData
from ..objects import IoPipelineHttpMessageEnd
from ..objects import IoPipelineHttpMessageHead
from ..objects import IoPipelineHttpMessageObjects
from .codings import DefaultIoPiplineHttpCompressionCodings
from .codings import IoPiplineHttpDecompressorCoding
from .codings import IoPiplineHttpDecompressorCodings


##


@dc.dataclass(frozen=True)
class IoPipelineHttpDecompressionConfig:
    DEFAULT: ta.ClassVar['IoPipelineHttpDecompressionConfig']

    max_decomp_chunk: int = 64 * 1024  # max bytes emitted per inflate step

    max_decomp_total: ta.Optional[int] = None    # max total decompressed bytes per object
    max_expansion_ratio: ta.Optional[int] = 200  # max_out <= max(1, in_total) * ratio (+ small slack)

    max_out_pending: ta.Optional[int] = 256 * 1024  # cap decompressed bytes retained by this stage (if you buffer)

    # CPU Bounding: how many decompress steps to perform before yielding to the driver
    max_steps_per_call: ta.Optional[int] = None

    # What to do with bytes following a complete compressed stream.
    #
    # For gzip these are legitimately the next member of a multi-member stream (RFC 1952 §2.2), so 'member' decodes
    # them as such. They may however also be junk, in which case 'member' surfaces the resulting decode failure -
    # urllib3 instead tolerates trailing bytes and silently stops at the first member's end. That leniency is exactly
    # what makes a truncated-to-one-member body indistinguishable from a complete one, so it is not the default.
    trailing_data: ta.Literal['member', 'ignore'] = 'member'

    def __post_init__(self) -> None:
        # A zero step budget would defer before ever taking a step - an infinite defer loop.
        if (msc := self.max_steps_per_call) is not None and msc < 1:
            raise ValueError(f'max_steps_per_call must be positive: {msc!r}')

        if self.trailing_data not in ('member', 'ignore'):
            raise ValueError(f'unknown trailing_data mode: {self.trailing_data!r}')


IoPipelineHttpDecompressionConfig.DEFAULT = IoPipelineHttpDecompressionConfig()


#


class IoPipelineHttpObjectDecompressor(
    IoPipelineHttpMessageObjects,
    InboundBytesBufferingIoPipelineHandler,
    Abstract,
):
    def __init__(
            self,
            codings: ta.Optional[IoPiplineHttpDecompressorCodings] = None,
            config: IoPipelineHttpDecompressionConfig = IoPipelineHttpDecompressionConfig.DEFAULT,
    ) -> None:
        super().__init__()

        self._config = config
        if codings is None:
            codings = DefaultIoPiplineHttpCompressionCodings.DECOMPRESSOR
        self._codings = codings

        self._coding: ta.Optional[ta.Callable[[], IoPiplineHttpDecompressorCoding]] = None
        self._decompressor: ta.Optional[IoPiplineHttpDecompressorCoding] = None

        # Statistics for budget checks
        self._in_total_bytes = 0
        self._out_total_bytes = 0

        # Internal buffering
        self._in_pending: collections.deque[BytesLike] = collections.deque()
        self._in_pending_bytes = 0
        self._out_pending: collections.deque[BytesLike] = collections.deque()
        self._out_pending_bytes = 0

        # Flow Control and Deferral State
        self._read_requested = False
        self._pending_end: ta.Optional[IoPipelineHttpMessageEnd] = None
        self._finished = False
        self._pending_final_input: ta.Optional[IoPipelineMessages.FinalInput] = None

    #

    def inbound_buffered_bytes(self) -> int:
        return self._in_pending_bytes + self._out_pending_bytes

    #

    def _reset(self, *, preserve_pending_final_input: bool = False) -> None:
        self._coding = None
        self._decompressor = None

        self._in_total_bytes = 0
        self._out_total_bytes = 0

        self._in_pending.clear()
        self._in_pending_bytes = 0
        self._out_pending.clear()
        self._out_pending_bytes = 0

        self._read_requested = False
        self._pending_end = None
        self._finished = False
        if not preserve_pending_final_input:
            self._pending_final_input = None

    def _check_budgets(self) -> None:
        if (mdt := self._config.max_decomp_total) is not None and self._out_total_bytes > mdt:
            raise ValueError('decompressor output exceeds limit (possible zip bomb)')

        if (mer := self._config.max_expansion_ratio) is not None:
            slack = self._config.max_decomp_chunk
            if self._out_total_bytes > (max(1, self._in_total_bytes) * mer + slack):
                raise ValueError('decompressor expansion ratio exceeds limit (possible zip bomb)')

    def _new_decompressor(self) -> IoPiplineHttpDecompressorCoding:
        if (coding := self._coding) is None:
            raise RuntimeError('no coding')
        return coding()

    def _is_auto_read(self, ctx: IoPipelineHandlerContext) -> bool:
        if (flow := ctx.services.find(IoPipelineFlow)) is None:
            return True
        return flow.is_auto_read()

    def _emit_out_pending(self, ctx: IoPipelineHandlerContext) -> bool:
        """Returns True if at least one message was emitted."""

        emitted = False

        while self._out_pending and (self._is_auto_read(ctx) or self._read_requested):
            o = self._out_pending.popleft()
            self._out_pending_bytes -= len(o)

            if not self._is_auto_read(ctx):
                self._read_requested = False

            ctx.feed_in(self._make_body_data(DirectByteStreamBufferView(o)))
            emitted = True

            # In manual mode, we satisfy one 'read' at a time.
            if not self._is_auto_read(ctx):
                break

        return emitted

    def _pump(self, ctx: IoPipelineHandlerContext) -> bool:
        """Returns True if it effectively satisfied a read request."""

        z = self._decompressor
        if z is None:
            return False

        steps = 0
        max_steps = self._config.max_steps_per_call

        # 1. Try to clear existing output.
        if self._emit_out_pending(ctx):
            if not self._is_auto_read(ctx):
                return True

        # 2. If blocked by downstream, we can't satisfy anything.
        if self._out_pending:
            return False

        # 3. Decompression Loop
        while self._in_pending:
            # Enforce output buffer budget
            if (mop := self._config.max_out_pending) is not None:
                if self._out_pending_bytes >= mop:
                    break

            # Check for CPU step limit
            if max_steps is not None and steps >= max_steps:
                self._defer_resume(ctx)
                return False  # We haven't satisfied it yet, we deferred.

            steps += 1
            chunk = self._in_pending.popleft()
            cl = len(chunk)
            self._in_pending_bytes -= cl

            out = z.decompress(chunk, self._config.max_decomp_chunk)
            if out:
                ol = len(out)
                self._out_total_bytes += ol
                self._out_pending.append(out)
                self._out_pending_bytes += ol
                self._check_budgets()

                if self._emit_out_pending(ctx):
                    if not self._is_auto_read(ctx):
                        return True  # Satisfied!

            if z.eof():
                # The current decompressor is spent: everything past its trailer lands in unused_data and it would
                # silently return nothing forever. Note that eof must be checked *before* unconsumed_tail - zlib
                # mirrors the leftover into both when the output limit was hit on the same call that ended the stream.
                if (ud := z.unused_data()):
                    self._in_pending.appendleft(ud)
                    self._in_pending_bytes += len(ud)

                if self._config.trailing_data == 'ignore':
                    self._in_pending.clear()
                    self._in_pending_bytes = 0
                    break

                if not self._in_pending:
                    break

                # A following member, concatenated either within this chunk or starting at the next one.
                z = self._decompressor = self._new_decompressor()

            elif (ut := z.unconsumed_tail()):
                self._in_pending.appendleft(ut)
                self._in_pending_bytes += len(ut)
                if not out:
                    break

        # 4. Finish and deliver the HTTP message end.
        if not self._in_pending and self._pending_end is not None:
            if not self._finished:
                if max_steps is not None and steps >= max_steps:
                    self._defer_resume(ctx)
                    return False

                out = z.finish()
                self._finished = True

                if not z.eof() and self._in_total_bytes:
                    # `finish` does not fail on an incomplete stream, so nothing else would notice a body truncated
                    # mid-stream - including gzip's own crc/length check, which lives in the trailer.
                    aborted = self._make_aborted('truncated compressed message body')
                    self._reset(preserve_pending_final_input=True)
                    ctx.feed_in(aborted)
                    return True

                if out:
                    ol = len(out)
                    self._out_total_bytes += ol
                    self._out_pending.append(out)
                    self._out_pending_bytes += ol
                    self._check_budgets()
                    if self._emit_out_pending(ctx) and not self._is_auto_read(ctx):
                        return True

            if self._out_pending:
                return False

            if not self._is_auto_read(ctx) and not self._read_requested:
                return False

            msg = self._pending_end
            self._reset(preserve_pending_final_input=True)
            ctx.feed_in(msg)
            return True  # End counts as satisfying the last read.

        return False

    def _defer_resume(self, ctx: IoPipelineHandlerContext) -> None:
        def resume(c: IoPipelineHandlerContext) -> None:
            if self._pump(c):
                # If a deferred pump satisfies a read, it must provide the FlushInput
                if not self._is_auto_read(c):
                    c.feed_in(IoPipelineFlowMessages.FlushInput())

                # A parked FinalInput has had its must-propagate tracking disarmed - if it is not released here the
                # connection's eof is simply lost. This is reached in auto-read too, where the pump only completes via
                # deferral.
                self._release_pending_final_input(c)

        ctx.defer(resume)

    #

    def _release_pending_final_input(self, ctx: IoPipelineHandlerContext) -> None:
        if self._decompressor is not None or self._pending_final_input is None:
            return

        msg = self._pending_final_input
        self._pending_final_input = None
        ctx.feed_in(msg)

    #

    def _on_inbound_final_input(self, ctx: IoPipelineHandlerContext, msg: IoPipelineMessages.FinalInput) -> None:
        if self._decompressor is None:
            ctx.feed_in(msg)
            return

        if self._pending_end is not None:
            ctx.mark_propagated('inbound', msg)
            self._pending_final_input = msg
            return

        self._reset()

        ctx.feed_in(self._make_aborted('eof before end of message'))
        ctx.feed_in(msg)

    def _on_inbound_flush_input(self, ctx: IoPipelineHandlerContext, msg: IoPipelineFlowMessages.FlushInput) -> None:
        self._pump(ctx)
        ctx.feed_in(msg)

    def _on_inbound_head(self, ctx: IoPipelineHandlerContext, msg: IoPipelineHttpMessageHead) -> None:
        if self._decompressor is not None:
            ctx.feed_in(self._make_aborted('unexpected message sequence'))
            return

        enc = msg.headers.lower.get('content-encoding', ())

        # TODO: spec is actually an ordered stack lol
        for coding_name, coding in self._codings.items():
            if coding_name.lower() in enc:
                self._coding = coding
                self._decompressor = coding()
                break

        ctx.feed_in(msg)

    def _on_inbound_body_data(self, ctx: IoPipelineHandlerContext, msg: IoPipelineHttpMessageBodyData) -> None:
        if self._decompressor is None:
            ctx.feed_in(msg)
            return

        for mv in ByteStreamBuffers.iter_segments(msg.data):
            mvl = len(mv)
            self._in_total_bytes += mvl
            self._in_pending.append(mv)
            self._in_pending_bytes += mvl
            self._check_budgets()

        self._pump(ctx)

    def _on_inbound_end(self, ctx: IoPipelineHandlerContext, msg: IoPipelineHttpMessageEnd) -> None:
        if self._decompressor is None:
            ctx.feed_in(msg)
            return

        self._pending_end = msg
        self._pump(ctx)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._on_inbound_final_input(ctx, msg)

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._on_inbound_flush_input(ctx, msg)

        elif isinstance(msg, self._head_type):
            self._on_inbound_head(ctx, msg)

        elif isinstance(msg, self._body_data_type):
            self._on_inbound_body_data(ctx, msg)

        elif isinstance(msg, self._end_type):
            self._on_inbound_end(ctx, msg)

        else:
            ctx.feed_in(msg)

    #

    def _on_outbound_ready_for_input(self, ctx: IoPipelineHandlerContext, msg: IoPipelineFlowMessages.ReadyForInput) -> None:  # Noqa
        self._read_requested = True

        if (
                self._out_pending or
                (
                    self._decompressor is not None and
                    (self._in_pending or self._pending_end is not None)
                )
        ):
            if self._pump(ctx):
                if not self._is_auto_read(ctx):
                    ctx.feed_in(IoPipelineFlowMessages.FlushInput())
                    self._release_pending_final_input(ctx)

                return  # Swallow since we satisfied it

        ctx.feed_out(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineFlowMessages.ReadyForInput):
            self._on_outbound_ready_for_input(ctx, msg)

        else:
            ctx.feed_out(msg)
