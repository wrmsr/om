# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""
Demonstrations of open findings from reviewing the half-close and multiplexing work: each test here fails on purpose
until its finding is resolved. See FINDINGS.md for the discussion.
"""
import typing as ta
import unittest

from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineMessages


##


class _Command(IoPipelineMessages.AfterFinalInput):
    """An out-of-band request injected at a handler's position, as `MultiplexMessages.OpenStream` is."""


class _Recorder(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.seen: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self.seen.append(msg)
        if isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


class TestInjectedInputBeforeInitialInput(unittest.TestCase):
    # `IoPipeline.feed_in_to` injects a message at a handler's position - the multiplexing README documents it as the
    # way to open a stream from outside the pipeline. Doing so before the driver has fed InitialInput (which every
    # driver does on its first step, after the pipeline exists) counts as "input", so the InitialInput which follows is
    # rejected and the driver fails. An injected request is not transport input and should not begin the input
    # lifetime.

    def test_injected_request_then_initial_input(self) -> None:
        rec = _Recorder()
        p = IoPipeline.new([rec])
        ref = p.handlers()[0]

        p.feed_in_to(ref, _Command())
        p.feed_initial_input()

        self.assertEqual([type(m) for m in rec.seen], [_Command, IoPipelineMessages.InitialInput])
        self.assertTrue(p.saw_initial_input)
