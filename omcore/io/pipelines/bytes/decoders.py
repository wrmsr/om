# ruff: noqa: FURB188 UP006 UP037 UP045
# @om-lite
"""
TODO: Dynamic decoder removal / Netty pending-removal semantics.

The recirculation in ``BytesToMessageDecoderIoPipelineHandler._call_decode`` does not implement Netty's
``STATE_HANDLER_REMOVED_PENDING`` trick. It solves a different ordering problem: reentrant ``FlushInput`` and
``FinalInput`` messages are queued until the active decode and its output delivery finish. Reentrant byte input is not
queued; it either uses the explicitly enabled reentrant-decode path or raises ``RuntimeError``.

Netty's ``ByteToMessageDecoder`` has separate protection for removal during ``decode()``. If removal is requested while
the decoder is on the stack, it marks removal pending. After ``decode()`` returns, it first forwards any messages that
were already decoded, then runs removal cleanup and forwards the remaining undecoded cumulation as raw bytes. Netty's
reentrant ``channelRead`` input queue is the mechanism analogous to the recirculation here, not its pending-removal
state.

This cannot be fixed entirely inside this decoder. ``IoPipeline._remove`` currently unlinks and invalidates a context,
and deletes its neighbor links, before notifying the handler that it was removed. Consequently the old context cannot be
used to finish delivering decoded output or to drain residual bytes. In particular:

 - A decoder which removes itself from ``_decode`` can fail in ``ctx.feed_in`` because ``_next_in`` was deleted.
 - If a downstream handler removes the decoder while consuming the first of multiple decoded messages, the first can be
   delivered while delivery of the rest fails.
 - Removing a buffered decoder with unread cumulation silently strands those bytes in the removed handler.
 - The eventual ``Removed`` notification is too late to drain through the handler's former pipeline position.

The topology-mutation contract should be decided in the core before implementing a decoder-local removal state. The
recommended contract is:

 1. Removal requested during a handler invocation becomes pending rather than immediately destroying its routing
    context.
 2. Already-produced messages retain their order and are forwarded before removal cleanup. 3. A pre-unlink removal phase
    has a stable successor route through which handler-owned state can be drained or transferred. Ordinary handler
    callbacks must not resume after the handler has entered removal.
 4. A buffered byte decoder forwards its remaining undecoded cumulation as raw bytes, matching Netty and supporting
    protocol-upgrade boundaries such as STARTTLS.
 5. Stateful protocol transforms such as compression and TLS either define safe drainage/completion semantics or reject
    removal outside a quiescent state.
 6. Outbound buffers likewise need an explicit drain, failure, or rejection policy; removal must not silently lose
    bytes, pending flush/final fences, or a previously announced paused state.

Dynamic addition also needs a flow-state contract. Output writability is currently communicated as edges, while a newly
inserted buffering handler initializes its downstream as writable. If it is inserted while downstream is already paused,
it misses that edge and can later announce a false ``ReadyForOutput`` when its local buffer drains (and can emit a
duplicate ``PauseOutput`` while filling). Either current downstream writability must be queryable/replayed on addition,
or live mutation must be constrained to a defined quiescent point with a known writable baseline.

Coverage associated with this work should include:

 - Core add/remove/replace during both inbound and outbound handler calls, including self-removal, downstream-triggered
   removal during multi-message delivery, notification ordering, exception behavior, stable successor routing, and
   reference release with cyclic GC disabled.
 - Decoder removal while idle, with unread cumulation, from inside ``_decode`` after producing zero/one/multiple
   messages, from downstream while consuming the first decoded message, and with reentrant flush/final messages queued.
 - Decoder replacement across a byte-split protocol-upgrade boundary.
 - Outbound-buffer removal while empty, nonempty, locally paused, and downstream-paused; addition while downstream is
   paused; replacement of one buffering handler by another; and pending ``FlushOutput``/``FinalOutput`` completion.
 - The corresponding pending-state cases for chunking, compression, decompression, and TLS, with tests documenting which
   transforms permit live removal and which require quiescence.

Existing tests cover ordinary topology changes and steady-state buffering/watermark behavior, but do not exercise these
interactions. Do not remove this to-do merely because input recirculation exists; it represents a broader, currently
undefined topology-mutation and buffered-state contract.
"""
import abc
import collections
import typing as ta

from ....lite.abstract import Abstract
from ....lite.check import check
from ...streambufs.direct import DirectByteStreamBuffer
from ...streambufs.framing import LongestMatchDelimiterByteStreamFrameDecoder
from ...streambufs.scanning import ScanningByteStreamBuffer
from ...streambufs.segmented import SegmentedByteStreamBuffer
from ...streambufs.types import ByteStreamBuffer
from ...streambufs.types import MutableByteStreamBuffer
from ...streambufs.utils import ByteStreamBuffers
from ...streambufs.utils import CanByteStreamBuffer
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineMessages
from ..errors import IncompleteDecodingIoPipelineError
from ..flow.types import IoPipelineFlow
from ..flow.types import IoPipelineFlowMessages
from .buffering import InboundBytesBufferingIoPipelineHandler


##


class UnicodeDecoderIoPipelineHandler(IoPipelineHandler):
    """bytes/view -> str (UTF-8, replacement)."""

    def __init__(
            self,
            encoding: str = 'utf-8',
            *,
            errors: ta.Literal['strict', 'ignore', 'replace'] = 'strict',
    ) -> None:
        super().__init__()

        self._encoding = encoding
        self._errors = errors

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if ByteStreamBuffers.can_bytes(msg):
            b = ByteStreamBuffers.to_bytes(msg)

            msg = b.decode(self._encoding, errors=self._errors)

        ctx.feed_in(msg)


##


class DelimiterFrameDecoderIoPipelineHandler(InboundBytesBufferingIoPipelineHandler):
    """
    bytes-like -> frames using longest-match delimiter semantics.

    TODO:
     - flow control, *or* replace with BytesToMessageDecoderIoPipelineHandler
    """

    def __init__(
            self,
            delims: ta.Sequence[bytes],
            *,
            keep_ends: bool = False,
            max_size: ta.Optional[int] = None,
            max_buffer: ta.Optional[int] = None,
            buffer_chunk_size: int = 64 * 1024,
            on_incomplete_final: ta.Literal['allow', 'raise'] = 'allow',
    ) -> None:
        super().__init__()

        self._on_incomplete_final = on_incomplete_final

        self._buf = ScanningByteStreamBuffer(SegmentedByteStreamBuffer(
            max_size=max_buffer,
            chunk_size=buffer_chunk_size,
        ))

        self._fr = LongestMatchDelimiterByteStreamFrameDecoder(
            delims,
            keep_ends=keep_ends,
            max_size=max_size,
        )

    def inbound_buffered_bytes(self) -> int:
        return len(self._buf)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._produce_frames(ctx, final=True)
            ctx.feed_in(msg)
            return

        if not ByteStreamBuffers.can_bytes(msg):
            ctx.feed_in(msg)
            return

        for mv in ByteStreamBuffers.iter_segments(msg):
            if mv:
                self._buf.write(mv)

        self._produce_frames(ctx)

    def _produce_frames(self, ctx: IoPipelineHandlerContext, *, final: bool = False) -> None:
        frames = self._fr.decode(self._buf, final=final)

        if final and len(self._buf):
            if (oif := self._on_incomplete_final) == 'allow':
                frames.append(self._buf.split_to(len(self._buf)))
            elif oif == 'raise':
                raise IncompleteDecodingIoPipelineError
            else:
                raise RuntimeError(f'unexpected on_incomplete_final: {oif!r}')

        for fr in frames:
            ctx.feed_in(fr)


##


class BytesToMessageDecoderIoPipelineHandler(IoPipelineHandler, Abstract):
    @abc.abstractmethod
    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        raise NotImplementedError

    #

    _decode_state: ta.Literal['ready', 'decoding'] = 'ready'

    _allow_decode_reentrance: bool = False
    _decode_output: ta.Optional['collections.deque[ta.Any]'] = None
    _decode_pending_input: ta.Optional['collections.deque[ta.Any]'] = None

    _called_decode: bool = False  # ~ `selfFiredChannelRead`
    _produced_messages: bool = False  # ~ `firedChannelRead`

    def _call_decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            *,
            final: bool = False,
    ) -> None:
        if self._decode_state == 'ready':
            check.none(self._decode_output)
            check.none(self._decode_pending_input)

            self._decode_state = 'decoding'
            doq: 'collections.deque[ta.Any]' = collections.deque()
            diq: 'collections.deque[ta.Any]' = collections.deque()
            self._decode_output = doq
            self._decode_pending_input = diq

            self._called_decode = True

            try:
                out: ta.List[ta.Any] = []
                self._decode(ctx, data, out, final=final)
                doq.extend(out)

                if not doq:
                    return

                self._produced_messages = True

                while doq:
                    out_msg = doq.popleft()
                    ctx.feed_in(out_msg)

            finally:
                self._decode_output = None
                self._decode_pending_input = None
                self._decode_state = 'ready'

                while diq:
                    in_msg = diq.popleft()
                    self.inbound(ctx, in_msg)

        elif self._decode_state == 'decoding':
            if not self._allow_decode_reentrance:
                raise RuntimeError('already decoding')

            doq = check.not_none(self._decode_output)

            out = []
            self._decode(ctx, data, out, final=final)
            doq.extend(out)

        else:
            raise RuntimeError(f'unexpected decode state: {self._decode_state!r}')

    #

    def _on_bytes_input(self, ctx: IoPipelineHandlerContext, data: CanByteStreamBuffer) -> None:
        check.arg(len(data) > 0)

        self._call_decode(ctx, data)

    def _on_flush_input(self, ctx: IoPipelineHandlerContext) -> None:
        if (
                self._called_decode and
                not self._produced_messages and
                not ctx.services[IoPipelineFlow].is_auto_read()
        ):
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

        self._called_decode = False
        self._produced_messages = False

        ctx.feed_in(IoPipelineFlowMessages.FlushInput())

    def _on_final_input(self, ctx: IoPipelineHandlerContext, msg: IoPipelineMessages.FinalInput) -> None:
        self._call_decode(ctx, DirectByteStreamBuffer(b''), final=True)

        ctx.feed_in(msg)

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            if (diq := self._decode_pending_input) is not None:
                diq.append(msg)
            else:
                self._on_flush_input(ctx)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            if (diq := self._decode_pending_input) is not None:
                diq.append(msg)
            else:
                self._on_final_input(ctx, msg)

        elif ByteStreamBuffers.can_bytes(msg):
            self._on_bytes_input(ctx, msg)

        else:
            ctx.feed_in(msg)


#


@ta.final
class FnBytesToMessageDecoderIoPipelineHandler(BytesToMessageDecoderIoPipelineHandler):
    class DecodeFn(ta.Protocol):
        def __call__(
                self,
                ctx: IoPipelineHandlerContext,
                data: CanByteStreamBuffer,
                out: ta.List[ta.Any],
                *,
                final: bool = False,
        ) -> None:
            ...

    def __init__(
            self,
            decode_fn: DecodeFn,
    ) -> None:
        super().__init__()

        self._decode_fn = decode_fn

    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            buf: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        self._decode_fn(ctx, buf, out, final=final)


##


class BufferedBytesToMessageDecoderIoPipelineHandler(
    InboundBytesBufferingIoPipelineHandler,
    BytesToMessageDecoderIoPipelineHandler,
    Abstract,
):
    def __init__(
            self,
            *,
            max_buffer_size: ta.Optional[int] = None,
            buffer_chunk_size: int = 64 * 1024,
            scanning_buffer: bool = False,
    ) -> None:
        super().__init__()

        self._max_buffer_size = max_buffer_size
        self._buffer_chunk_size = buffer_chunk_size
        self._scanning_buffer = scanning_buffer

    #

    def inbound_buffered_bytes(self) -> int:
        if (buf := self._buf) is None:
            return 0
        return len(buf)

    _buf: ta.Optional[MutableByteStreamBuffer] = None

    def _new_buf(self) -> MutableByteStreamBuffer:
        buf: MutableByteStreamBuffer = SegmentedByteStreamBuffer(
            max_size=self._max_buffer_size,
            chunk_size=self._buffer_chunk_size,
        )

        if self._scanning_buffer:
            buf = ScanningByteStreamBuffer(buf)

        return buf

    #

    def _decode(
            self,
            ctx: IoPipelineHandlerContext,
            data: CanByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        if final:
            check.arg(len(data) == 0)

            if not isinstance(data, ByteStreamBuffer):
                data = DirectByteStreamBuffer(b'')

            self._decode_buffer(ctx, data, out, final=final)

            return

        check.arg(len(data) > 0)

        if (buf := self._buf) is None:
            buf = self._buf = self._new_buf()

        for seg in ByteStreamBuffers.iter_segments(data):
            buf.write(seg)

        self._decode_buffer(ctx, buf, out, final=final)

    #

    @abc.abstractmethod
    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        raise NotImplementedError
