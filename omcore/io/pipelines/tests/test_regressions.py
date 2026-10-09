# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
"""Regression tests for defects found reviewing the half-close and multiplexing work. See FINDINGS.md."""
import typing as ta
import unittest

from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineMessages
from ..drivers.pure import PureIoPipelineDriver
from ..drivers.types import IoPipelineDriverState
from ..errors import SawFinalOutputIoPipelineError


##


class _ClosesTwice(IoPipelineHandler):
    """Sends two FinalOutputs on InitialInput, recording what comes back."""

    def __init__(self) -> None:
        super().__init__()

        self.first = IoPipelineMessages.FinalOutput()
        self.second = IoPipelineMessages.FinalOutput()
        self.errors: ta.List[IoPipelineMessages.Error] = []

        # Outcomes are only observable from listeners (DESIGN 5).
        self.second_exc: ta.Optional[BaseException] = None
        self.second.add_listener(self._on_second_done)

    def _on_second_done(self, msg: IoPipelineMessages.Completable) -> None:
        if msg.is_failed():
            self.second_exc = msg.get_exception()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self.first)
            ctx.feed_out(self.second)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            return

        ctx.feed_in(msg)


class TestSecondFinalOutput(unittest.TestCase):
    # DESIGN 4: "Once it reaches the outbound terminal, no further outbound message may reach that terminal." A second
    # FinalOutput is such a message, and must be rejected like anything else - not appended to the output queue, where
    # every driver then fails on it.

    def test_second_final_output_is_rejected_at_the_terminal(self) -> None:
        h = _ClosesTwice()
        p = IoPipeline.new([h])
        p.feed_initial_input()

        out = p.output.drain()
        self.assertEqual(out, [h.first])
        self.assertFalse(h.first.is_done())

        self.assertTrue(h.second.is_failed())
        self.assertIsInstance(h.second_exc, SawFinalOutputIoPipelineError)
        (err,) = h.errors
        self.assertIsInstance(err.exc, SawFinalOutputIoPipelineError)
        self.assertEqual(err.direction, 'outbound')

    def test_driver_closes_gracefully_after_a_second_final_output(self) -> None:
        h = _ClosesTwice()
        d = PureIoPipelineDriver(IoPipeline.Spec([h]))
        try:
            self.assertIsNone(d.next(read=True, raise_on_stall=False))
            self.assertIs(d.state, IoPipelineDriverState.DRAINING)
            d.drain_output()
            self.assertIs(d.state, IoPipelineDriverState.CLOSED)
            self.assertTrue(h.first.is_succeeded())
            self.assertTrue(h.second.is_failed())
        finally:
            d.close()
