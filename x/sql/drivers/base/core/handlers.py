"""
The protocol as omcore.io.pipelines handlers: a frontend message encoder, a backend message framer/decoder, and a
session handler which drives ProtocolSession operations. These are synchronous and transport-agnostic; sync and async
connections differ only in the pipeline driver they are attached to.
"""
import functools
import math
import typing as ta
import weakref

from omcore import check
from omcore import dataclasses as dc
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.errors import TimeoutIoPipelineError
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages
from omcore.io.pipelines.sched.types import IoPipelineScheduling
from omcore.io.streambufs.utils import ByteStreamBuffers


OperationT = ta.TypeVar('OperationT')


##


@dc.dataclass(frozen=True)
class OperationRequest(ta.Generic[OperationT]):
    """Fed inbound by a connection to start an operation."""

    op: OperationT


@dc.dataclass(frozen=True)
class OperationDone(ta.Generic[OperationT]):
    """Emitted to the pipeline output once an operation has finished, successfully or not."""

    op: OperationT


class OperationTimeoutsIoPipelineHandler(IoPipelineHandler, ta.Generic[OperationT]):
    """
    Enforces read and write deadlines while an operation is in flight.

    Placed on the transport side of the codec handlers so its read activity is raw transport input; when a TLS handler
    is later added outermost, that activity becomes the decrypted stream, and a stalled TLS handshake is still caught
    because the deadline of whichever operation drove the handshake keeps running.

    The read deadline is armed while an operation is in flight and reset by each inbound chunk, so it times out a
    transport gone quiet mid-operation, not a slow-but-flowing response. Writes are covered by flush fences: each burst
    of outbound data is followed by a FlushOutput fence, which the transport driver completes once everything before it
    has crossed the transport, and a fence outstanding for longer than the write timeout fails the pipeline. With
    neither timeout configured the handler is a scheduler-independent, tickless pass-through.
    """

    def __init__(
            self,
            *,
            read_timeout_s: float | None = None,
            write_timeout_s: float | None = None,
    ) -> None:
        super().__init__()

        for timeout_s in (read_timeout_s, write_timeout_s):
            if timeout_s is not None and (not math.isfinite(timeout_s) or timeout_s <= 0.):
                raise ValueError(timeout_s)
        self._read_timeout_s = read_timeout_s
        self._write_timeout_s = write_timeout_s

        self._active = False
        self._timed_out = False
        self._read_handle: IoPipelineScheduling.Handle | None = None
        self._write_handle: IoPipelineScheduling.Handle | None = None
        self._write_dirty = False

    #

    def _cancel_read(self) -> None:
        if (handle := self._read_handle) is not None:
            self._read_handle = None
            handle.cancel()

    def _cancel_write(self) -> None:
        if (handle := self._write_handle) is not None:
            self._write_handle = None
            handle.cancel()
        self._write_dirty = False

    def _reset(self) -> None:
        self._active = False
        self._timed_out = False
        self._cancel_read()
        self._cancel_write()

    def _arm_read(self, ctx: IoPipelineHandlerContext) -> None:
        self._cancel_read()
        if self._read_timeout_s is None:
            return

        self._read_handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            self._read_timeout_s,
            lambda ctx2: check.isinstance(ctx2.handler, OperationTimeoutsIoPipelineHandler)._on_read_timeout(ctx2),  # noqa
        )

    def _on_read_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._read_handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Read timed out after {check.not_none(self._read_timeout_s):g} seconds'),
            direction='inbound',
            handler=ctx.ref,
        ))

    def _on_write_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._write_handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Write timed out after {check.not_none(self._write_timeout_s):g} seconds'),
            direction='outbound',
            handler=ctx.ref,
        ))

    @staticmethod
    def _on_fence_done(
            ctx_ref: ta.Callable[[], IoPipelineHandlerContext | None],
            _msg: IoPipelineMessages.Completable[None],
    ) -> None:
        if (ctx := ctx_ref()) is None or ctx.invalidated:
            return

        handler = check.isinstance(ctx.handler, OperationTimeoutsIoPipelineHandler)
        if (handle := handler._write_handle) is not None:  # noqa: SLF001
            handler._write_handle = None  # noqa: SLF001
            handle.cancel()

        # More output passed while this fence was pending; cover it with a fresh fence and deadline.
        if handler._write_dirty and handler._active and not handler._timed_out:  # noqa: SLF001
            handler._emit_write_fence(ctx)  # noqa: SLF001

    def _emit_write_fence(self, ctx: IoPipelineHandlerContext) -> None:
        self._write_dirty = False
        self._write_handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            check.not_none(self._write_timeout_s),
            lambda ctx2: check.isinstance(ctx2.handler, OperationTimeoutsIoPipelineHandler)._on_write_timeout(ctx2),  # noqa
        )
        fence = IoPipelineFlowMessages.FlushOutput()
        fence.add_listener(functools.partial(self._on_fence_done, weakref.ref(ctx)))
        ctx.feed_out(fence)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if self._read_timeout_s is not None or self._write_timeout_s is not None:
                check.not_none(ctx.services.find(IoPipelineScheduling))
            self._reset()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._reset()

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OperationRequest):
            self._active = True
            self._timed_out = False
            self._arm_read(ctx)

        elif isinstance(msg, (IoPipelineMessages.Error, IoPipelineMessages.FinalInput)):
            self._reset()

        elif self._active and not self._timed_out and ByteStreamBuffers.can_bytes(msg):
            self._arm_read(ctx)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, OperationDone):
            self._reset()
            ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._reset()
            ctx.feed_out(msg)
            return

        ctx.feed_out(msg)

        if (
                self._write_timeout_s is not None and
                self._active and
                not self._timed_out and
                ByteStreamBuffers.can_bytes(msg)
        ):
            if self._write_handle is None:
                self._emit_write_fence(ctx)
            else:
                self._write_dirty = True
