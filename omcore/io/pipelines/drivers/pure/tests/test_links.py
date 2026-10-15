# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import typing as ta
import unittest

from ....core import IoPipeline
from ....core import IoPipelineHandler
from ....core import IoPipelineHandlerContext
from ....flow.types import IoPipelineFlowMessages
from ..drivers import PureIoPipelineDriver
from ..links import PureLink


##


class _SendOnCommand(IoPipelineHandler):
    def __init__(self, fence: IoPipelineFlowMessages.FlushOutput) -> None:
        super().__init__()

        self._fence = fence

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg == 'send':
            ctx.feed_out(b'payload')
            ctx.feed_out(self._fence)
        else:
            ctx.feed_in(msg)


class TestPureLink(unittest.TestCase):
    def test_flush_does_not_succeed_after_peer_has_closed(self) -> None:
        fence = IoPipelineFlowMessages.FlushOutput()
        a = PureIoPipelineDriver(IoPipeline.Spec([_SendOnCommand(fence)]))
        b = PureIoPipelineDriver(IoPipeline.Spec())
        link = PureLink(a, b)
        try:
            self.assertIsNone(a.next(read=False))
            self.assertIsNone(b.next(read=False))
            b.close()

            a.enqueue('send')
            link.pump_once()

            self.assertTrue(fence.is_failed())
        finally:
            a.close()
            b.close()
