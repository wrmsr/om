# ruff: noqa: SLF001 UP006 UP037 UP045
"""
Regression tests for a confirmed driver bug (see omcore/io/pipelines/FINDINGS.md, finding F1).

A duplicate FinalOutput reaching a driver fails it with a bare `ValueError: Must be None` instead of a routed pipeline
error, on the pure, sync, and fdio drivers. The asyncio driver handles it gracefully (the first FinalOutput succeeds,
the second is failed by pipeline destruction). The pipeline terminal itself tolerates a second FinalOutput - it only
rejects messages sent *after* one - so the drivers' `check.none(self._transport_final_output)` is the inconsistency.

These tests document current (buggy) behavior where it crashes, and desired behavior where it does not. They are
integration tests: real pipelines over a real socket pair / pure driver, no mocks.
"""
import socket
import typing as ta
import unittest

from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..pure import PureIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver


class _DupFinalApp(IoPipelineHandler):
    """On InitialInput, feeds two FinalOutput messages back to back (an application bug, on purpose)."""

    def __init__(self) -> None:
        super().__init__()

        self.errors: ta.List[BaseException] = []
        self.first = IoPipelineMessages.FinalOutput()
        self.second = IoPipelineMessages.FinalOutput()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return

        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self.first)
            ctx.feed_out(self.second)
            return

        if isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


class TestDuplicateFinalOutput(unittest.TestCase):
    def test_pure_driver_duplicate_final_output(self) -> None:
        app = _DupFinalApp()
        driver = PureIoPipelineDriver(IoPipeline.Spec([app], services=[StubIoPipelineFlowService()]))
        try:
            # The duplicate FinalOutput must not crash the driver with a bare ValueError.
            driver.next(raise_on_stall=False)
        finally:
            driver.close()

    def test_sync_driver_duplicate_final_output(self) -> None:
        app = _DupFinalApp()
        sock, peer = socket.socketpair()
        try:
            driver = SocketSyncIoPipelineDriver(
                IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=False)]),
                sock,
            )
            try:
                driver.next(read=False)
            finally:
                driver.close()
        finally:
            peer.close()

    def test_fdio_driver_duplicate_final_output(self) -> None:
        app = _DupFinalApp()
        sock, peer = socket.socketpair()
        sock.setblocking(False)
        peer.setblocking(False)
        try:
            driver = IoPipelineDriverSocketFdioHandler(
                sock,
                ('peer', 0),
                IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=False)]),
            )
            try:
                # First poll returns 'stop' for the first FinalOutput; the second poll hits the duplicate.
                driver.poll()
                driver.poll()
            finally:
                driver.close()
        finally:
            peer.close()


if __name__ == '__main__':
    unittest.main()
