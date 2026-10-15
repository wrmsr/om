# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
import typing as ta
import unittest

from ......sockets.endpoints import TcpSocketEndpoint
from ......sockets.endpoints import UnixSocketEndpoint
from ....core import IoPipeline
from ....core import IoPipelineHandler
from ....core import IoPipelineHandlerContext
from ....core import IoPipelineMessages
from ....hosts.types import ConnectIoPipelineHostError
from ....hosts.types import IoPipelineHostedDriver
from ....hosts.types import ListenIoPipelineHostError
from ....posting.types import IoPipelinePosting
from ...types import IoPipelineDriverState
from ..hosts import MemoryIoPipelineHost


##


class _Marker:
    pass


class _EmitApp(IoPipelineHandler):
    """Feeds a marker out, unhandled by any driver, on start."""

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_out(_Marker())
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


class TestMemoryIoPipelineHost(unittest.TestCase):
    def test_outcomes_are_not_delivered_inside_the_request(self) -> None:
        host = MemoryIoPipelineHost()
        try:
            failed: ta.List[BaseException] = []
            host.connect(
                TcpSocketEndpoint('127.0.0.1', 9),
                lambda info: IoPipeline.Spec(),
                on_connected=lambda c, h: None,
                on_failed=lambda c, e: failed.append(e),
            )
            self.assertEqual(failed, [])
            self.assertTrue(host.step())
            self.assertIsInstance(failed[0], ConnectIoPipelineHostError)
            self.assertFalse(host.step())
        finally:
            host.close()

    def test_port_zero_allocates_distinct_ports(self) -> None:
        host = MemoryIoPipelineHost()
        try:
            a = host.listen(TcpSocketEndpoint('127.0.0.1', 0), lambda info: IoPipeline.Spec())
            b = host.listen(TcpSocketEndpoint('127.0.0.1', 0), lambda info: IoPipeline.Spec())
            self.assertNotEqual(a.bound_endpoint, b.bound_endpoint)
            self.assertNotEqual(ta.cast(TcpSocketEndpoint, a.bound_endpoint).port, 0)

            with self.assertRaises(ListenIoPipelineHostError):
                host.listen(a.bound_endpoint, lambda info: IoPipeline.Spec())
            a.close()
            host.listen(a.bound_endpoint, lambda info: IoPipeline.Spec())
        finally:
            host.close()

    def test_unix_endpoints(self) -> None:
        host = MemoryIoPipelineHost()
        try:
            ep = UnixSocketEndpoint('memory.sock')
            listener = host.listen(ep, lambda info: IoPipeline.Spec())
            self.assertEqual(listener.bound_endpoint, ep)
            connected: ta.List[IoPipelineHostedDriver] = []
            host.connect(ep, lambda info: IoPipeline.Spec(), on_connected=lambda c, h: connected.append(h), on_failed=lambda c, e: None)  # noqa
            host.run()
            self.assertEqual(len(connected), 1)
        finally:
            host.close()

    def test_unhandled_output_of_an_unlinked_driver_is_collected(self) -> None:
        host = MemoryIoPipelineHost()
        try:
            a, b = host.pair()
            handle = host.adopt(a, IoPipeline.Spec([_EmitApp()]))
            host.run()
            self.assertEqual(len(ta.cast(ta.Any, handle).unhandled), 1)
            self.assertIsInstance(ta.cast(ta.Any, handle).unhandled[0], _Marker)
            self.assertFalse(b.adopted)
        finally:
            host.close()

    def test_advance_time_runs_hosted_timers(self) -> None:
        from ....sched.types import IoPipelineScheduling

        fired: ta.List[float] = []

        class TimerApp(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, IoPipelineMessages.InitialInput):
                    ctx.services[IoPipelineScheduling].schedule(ctx.ref, 2., lambda: fired.append(2.))
                if isinstance(msg, IoPipelineMessages.MayPropagate):
                    ctx.feed_in(msg)

        host = MemoryIoPipelineHost()
        try:
            a, _ = host.pair()
            host.adopt(a, IoPipeline.Spec([TimerApp()]))
            host.run()
            self.assertEqual(fired, [])
            host.advance_time(1.)
            host.run()
            self.assertEqual(fired, [])
            host.advance_time(1.)
            host.run()
            self.assertEqual(fired, [2.])
        finally:
            host.close()

    def test_posting_into_a_hosted_driver(self) -> None:
        host = MemoryIoPipelineHost()
        try:
            a, _ = host.pair()
            handle = host.adopt(a, IoPipeline.Spec())
            ran: ta.List[int] = []
            post = handle.posting.post(lambda: ran.append(1))
            self.assertEqual(ran, [])
            host.run()
            self.assertEqual(ran, [1])
            self.assertTrue(post.is_succeeded())
            self.assertIs(handle.state, IoPipelineDriverState.RUNNING)
            self.assertIs(ta.cast(IoPipeline, handle.pipeline).services[IoPipelinePosting], handle.posting)
        finally:
            host.close()

    def test_close_closes_hosted_drivers(self) -> None:
        host = MemoryIoPipelineHost()
        a, _ = host.pair()
        handle = host.adopt(a, IoPipeline.Spec())
        host.close()
        self.assertTrue(handle.closed)
        self.assertTrue(host.closed)
        host.close()
