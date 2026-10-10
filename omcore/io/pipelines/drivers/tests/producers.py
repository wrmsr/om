# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""Producers used by driver and multiplexer backpressure tests."""
import typing as ta

from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...flow.types import IoPipelineFlowMessages


##


DEFER_CHUNK = b'x' * (16 * 1024)
DEFER_N_CHUNKS = 64  # 1 MiB total, far above the 64 KiB high watermark


class DeferYieldingProducer(IoPipelineHandler):
    """
    A producer which honors writability and yields to the driver between chunks: each step emits one chunk and a flush,
    then continues through a Defer - the same pattern the multiplex handler's turn budget relies on ("the parent's
    driver only reports writability after processing queued output").
    """

    def __init__(self) -> None:
        super().__init__()

        self.emitted = 0
        self.emitted_at_first_pause: ta.Optional[int] = None
        self._writable = True

    def _step(self, ctx: IoPipelineHandlerContext) -> None:
        if not self._writable or self.emitted >= DEFER_N_CHUNKS:
            return
        ctx.feed_out(DEFER_CHUNK)
        self.emitted += 1
        ctx.feed_out(IoPipelineFlowMessages.FlushOutput())
        ctx.defer(self._step)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            self._step(ctx)
            return

        if isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._writable = False
            if self.emitted_at_first_pause is None:
                self.emitted_at_first_pause = self.emitted
            return

        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._writable = True
            self._step(ctx)
            return

        ctx.feed_in(msg)
