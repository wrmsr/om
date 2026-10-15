# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
import os
import socket
import tempfile
import threading
import time
import typing as ta
import unittest

from ......sockets.endpoints import TcpSocketEndpoint
from ......sockets.endpoints import UnixSocketEndpoint
from .....fdio.manager import FdioManager
from .....fdio.pollers import SelectFdioPoller
from .....fdio.wakeups import WakeupFdioHandler
from ....core import IoPipeline
from ....core import IoPipelineHandler
from ....core import IoPipelineHandlerContext
from ....core import IoPipelineMessages
from ....hosts.types import ConnectIoPipelineHostError
from ....hosts.types import IoPipelineHostedDriver
from ....hosts.types import ResolveIoPipelineHostError
from ...types import IoPipelineDriverState
from ..hosts import FdioIoPipelineHost
from ..resolvers import ThreadedFdioIoPipelineHostResolver
from ..running import fdio_run_until
from .test_pairs import _UpperEchoApp


##


class TestWakeupFdioHandler(unittest.TestCase):
    def test_post_from_another_thread_wakes_an_idle_manager(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        wakeup = WakeupFdioHandler()
        manager.register(wakeup)
        try:
            ran: ta.List[str] = []

            def later() -> None:
                time.sleep(.01)
                wakeup.post(lambda: ran.append(threading.current_thread().name))

            t = threading.Thread(target=later)
            started = time.monotonic()
            t.start()
            try:
                manager.poll(timeout=5.)
            finally:
                t.join()

            self.assertLess(time.monotonic() - started, 4.)
            self.assertEqual(ran, [threading.current_thread().name])
        finally:
            wakeup.close()
            self.assertTrue(wakeup.closed)

    def test_wake_without_a_callback_returns_the_poll(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        wakeup = WakeupFdioHandler()
        manager.register(wakeup)
        try:
            wakeup.wake()
            wakeup.wake()  # Coalesced: the pipe holds one pending wake.
            started = time.monotonic()
            manager.poll(timeout=5.)
            self.assertLess(time.monotonic() - started, 4.)
        finally:
            wakeup.close()


class TestFdioRunUntil(unittest.TestCase):
    def test_returns_when_the_condition_holds(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        wakeup = WakeupFdioHandler()
        manager.register(wakeup)
        try:
            hits: ta.List[int] = []
            wakeup.post(lambda: hits.append(1))

            self.assertTrue(fdio_run_until(manager, lambda: bool(hits), timeout_s=5.))
            self.assertEqual(hits, [1])
        finally:
            wakeup.close()

    def test_times_out(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        wakeup = WakeupFdioHandler()
        manager.register(wakeup)
        try:
            started = time.monotonic()
            self.assertFalse(fdio_run_until(manager, lambda: False, timeout_s=.05))
            self.assertGreaterEqual(time.monotonic() - started, .04)
        finally:
            wakeup.close()

    def test_invalid_timeout(self) -> None:
        with self.assertRaises(ValueError):
            fdio_run_until(FdioManager(SelectFdioPoller()), lambda: True, timeout_s=-1.)


class TestThreadedResolver(unittest.TestCase):
    def test_resolves_on_the_manager_thread(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        resolver = ThreadedFdioIoPipelineHostResolver(manager)
        try:
            results: ta.List[ta.Any] = []
            threads: ta.List[str] = []

            def on_done(result: ta.Any) -> None:
                threads.append(threading.current_thread().name)
                results.append(result)

            resolver.resolve('127.0.0.1', 80, on_done)
            self.assertTrue(fdio_run_until(manager, lambda: bool(results), timeout_s=5.))

            self.assertEqual(threads, [threading.current_thread().name])
            addrs = results[0]
            self.assertNotIsInstance(addrs, BaseException)
            self.assertEqual(addrs[0][3][0], '127.0.0.1')
            self.assertEqual(addrs[0][3][1], 80)
        finally:
            resolver.close()
            self.assertTrue(resolver.closed)
            resolver.close()

    def test_failure_is_a_resolve_error(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        resolver = ThreadedFdioIoPipelineHostResolver(manager)
        try:
            results: ta.List[ta.Any] = []
            resolver.resolve('no-such-host.invalid', 80, results.append)
            self.assertTrue(fdio_run_until(manager, lambda: bool(results), timeout_s=10.))
            self.assertIsInstance(results[0], ResolveIoPipelineHostError)
        finally:
            resolver.close()

    def test_host_connects_through_it(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        resolver = ThreadedFdioIoPipelineHostResolver(manager)
        host = FdioIoPipelineHost(manager, resolver=resolver)
        try:
            with socket.create_server(('127.0.0.1', 0)) as listener:
                port = listener.getsockname()[1]
                connected: ta.List[IoPipelineHostedDriver] = []
                failed: ta.List[BaseException] = []
                host.connect(
                    TcpSocketEndpoint('localhost', port),
                    lambda info: IoPipeline.Spec([_UpperEchoApp()]),
                    on_connected=lambda c, h: connected.append(h),
                    on_failed=lambda c, e: failed.append(e),
                    timeout_s=5.,
                )
                self.assertTrue(fdio_run_until(manager, lambda: bool(connected or failed), timeout_s=10.))
                self.assertEqual(failed, [])
                self.assertIs(connected[0].state, IoPipelineDriverState.RUNNING)
                accepted, _ = listener.accept()
                accepted.close()
        finally:
            host.close()
            resolver.close()


class _FinishAtOnceApp(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)


class TestFdioIoPipelineHostAdoption(unittest.TestCase):
    def test_a_driver_ending_during_its_start_is_not_kept(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        host = FdioIoPipelineHost(manager)
        a, b = socket.socketpair()
        try:
            handle = host.adopt(a, IoPipeline.Spec([_FinishAtOnceApp()]), owned=True)
            self.assertTrue(handle.closed)
            self.assertEqual(list(host.handles), [])
            self.assertEqual(b.recv(16), b'')
        finally:
            host.close()
            b.close()

    def test_immediate_unix_connect_outcome_is_delivered_by_the_manager(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        host = FdioIoPipelineHost(manager)
        try:
            with tempfile.TemporaryDirectory() as directory:
                endpoint = UnixSocketEndpoint(os.path.join(directory, 'socket'))
                listener = host.listen(endpoint, lambda info: IoPipeline.Spec())
                connected: ta.List[IoPipelineHostedDriver] = []
                failed: ta.List[BaseException] = []
                host.connect(
                    listener.bound_endpoint,
                    lambda info: IoPipeline.Spec(),
                    on_connected=lambda ctx, handle: connected.append(handle),
                    on_failed=lambda ctx, exc: failed.append(exc),
                )

                self.assertEqual(connected, [])
                self.assertEqual(failed, [])
                self.assertTrue(fdio_run_until(manager, lambda: bool(connected or failed), timeout_s=5.))
                self.assertEqual(len(connected), 1)
                self.assertEqual(failed, [])
        finally:
            host.close()

    def test_adopts_a_caller_owned_socket_without_closing_it(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        host = FdioIoPipelineHost(manager)
        a, b = socket.socketpair()
        try:
            echo = _UpperEchoApp()
            handle = host.adopt(a, IoPipeline.Spec([echo]))
            b.sendall(b'hi')
            b.settimeout(5.)
            self.assertTrue(fdio_run_until(manager, lambda: bytes(echo.received) == b'hi', timeout_s=5.))
            self.assertEqual(b.recv(16), b'HI')

            handle.close()
            os.fstat(a.fileno())
            self.assertEqual(a.gettimeout(), None)
        finally:
            host.close()
            a.close()
            b.close()

    def test_adopts_a_descriptor_pair(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        host = FdioIoPipelineHost(manager)
        in_r, in_w = os.pipe()
        out_r, out_w = os.pipe()
        try:
            echo = _UpperEchoApp()
            handle = host.adopt((in_r, out_w), IoPipeline.Spec([echo]), owned=True)
            os.write(in_w, b'pipe')
            self.assertTrue(fdio_run_until(manager, lambda: bytes(echo.received) == b'pipe', timeout_s=5.))
            self.assertEqual(os.read(out_r, 16), b'PIPE')

            handle.close()
            with self.assertRaises(OSError):
                os.fstat(in_r)
        finally:
            host.close()
            for fd in (in_w, out_r):
                os.close(fd)

    def test_listen_failure_is_typed(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        host = FdioIoPipelineHost(manager)
        try:
            with socket.create_server(('127.0.0.1', 0)) as taken:
                port = taken.getsockname()[1]
                from ....hosts.types import ListenIoPipelineHostError
                with self.assertRaises(ListenIoPipelineHostError):
                    host.listen(TcpSocketEndpoint('127.0.0.1', port), lambda info: IoPipeline.Spec())
        finally:
            host.close()

    def test_unresolvable_host_fails_the_connect(self) -> None:
        manager = FdioManager(SelectFdioPoller())
        host = FdioIoPipelineHost(manager)
        try:
            failed: ta.List[BaseException] = []
            host.connect(
                TcpSocketEndpoint('no-such-host.invalid', 80),
                lambda info: IoPipeline.Spec(),
                on_connected=lambda c, h: None,
                on_failed=lambda c, e: failed.append(e),
            )
            self.assertEqual(len(failed), 1)
            self.assertIsInstance(failed[0], ConnectIoPipelineHostError)
            self.assertIsInstance(failed[0], ResolveIoPipelineHostError)
        finally:
            host.close()
