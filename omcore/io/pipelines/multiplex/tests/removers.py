# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""Handlers placed outside the multiplexer which disturb it as frames pass outward."""
import typing as ta

from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages


##


class RemoveMuxOnFrame(IoPipelineHandler):
    """Outside the multiplexer: removes it from the pipeline as soon as a matching frame passes outward."""

    def __init__(self, match: ta.Callable[[ta.Any], bool]) -> None:
        super().__init__()

        self._match = match
        self.removed = False
        self.errors: ta.List[BaseException] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return
        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)
        if not self.removed and self._match(msg):
            self.removed = True
            ctx.pipeline.remove(ctx.pipeline.handlers()[-1])  # the multiplexer, innermost


class FailOnFrame(IoPipelineHandler):
    """Outside the multiplexer, like a frame encoder: raises on a matching outbound frame."""

    def __init__(self, match: ta.Callable[[ta.Any], bool]) -> None:
        super().__init__()

        self._match = match
        self.raised = 0

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if self._match(msg):
            self.raised += 1
            raise RuntimeError('cannot encode frame')
        ctx.feed_out(msg)
