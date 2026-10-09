# ruff: noqa: SLF001 UP006 UP045
# @om-lite
import fcntl
import os
import threading
import typing as ta
import unittest

from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import UnsupportedIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...sched.timeouts import ReadTimeoutIoPipelineHandler
from ..sync import FdSyncIoPipelineDriver
from ..types import IoPipelineDriverState


class Echoed:
    """Returned from next() after each echo so tests can step deterministically."""

    def __init__(self, n: int) -> None:
        self.n = n


class UpperEchoIoPipelineHandler(IoPipelineHandler):
    """Echoes uppercased input back out, closes output on EOF, and surfaces errors as output."""

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return

        if isinstance(msg, IoPipelineMessages.Error):
            ctx.feed_out(msg.exc)
            return

        if ByteStreamBuffers.can_bytes(msg):
            data = ByteStreamBuffers.to_bytes(msg, strict=True)
            ctx.feed_out(data.upper())
            ctx.feed_out(Echoed(len(data)))
            return

        ctx.feed_in(msg)


def _step(drv: FdSyncIoPipelineDriver) -> ta.Any:
    """Wait for the next echo, then flush its output without waiting for further input."""

    out = drv.next()
    while drv.next(read=False) is not None:
        pass
    return out


class _Pipes:
    """Two pipes: the driver reads from `in` and writes to `out`; the test does the reverse."""

    def __init__(self) -> None:
        self.in_r, self.in_w = os.pipe()
        self.out_r, self.out_w = os.pipe()

    def close(self) -> None:
        for fd in (self.in_r, self.in_w, self.out_r, self.out_w):
            try:
                os.close(fd)
            except OSError:
                pass


class TestFdSyncIoPipelineDriver(unittest.TestCase):
    def test_echo_over_pipes(self) -> None:
        pipes = _Pipes()
        try:
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([UpperEchoIoPipelineHandler()], services=[StubIoPipelineFlowService()]),
                pipes.in_r,
                pipes.out_w,
            )

            os.write(pipes.in_w, b'hello')
            self.assertIsInstance(_step(drv), Echoed)
            self.assertEqual(os.read(pipes.out_r, 100), b'HELLO')

            os.write(pipes.in_w, b' world')
            self.assertIsInstance(_step(drv), Echoed)
            self.assertEqual(os.read(pipes.out_r, 100), b' WORLD')

            # EOF on input closes output gracefully. The descriptors are caller-owned and stay open.
            os.close(pipes.in_w)
            drv.loop_until_done()
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            os.close(pipes.out_w)
            self.assertEqual(os.read(pipes.out_r, 100), b'')

        finally:
            pipes.close()

    def test_restores_blocking_flags(self) -> None:
        pipes = _Pipes()
        try:
            before = {fd: fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK for fd in (pipes.in_r, pipes.out_w)}
            self.assertEqual(set(before.values()), {0})

            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([UpperEchoIoPipelineHandler()]),
                pipes.in_r,
                pipes.out_w,
            )
            os.write(pipes.in_w, b'x')
            _step(drv)
            self.assertTrue(fcntl.fcntl(pipes.in_r, fcntl.F_GETFL) & os.O_NONBLOCK)
            self.assertTrue(fcntl.fcntl(pipes.out_w, fcntl.F_GETFL) & os.O_NONBLOCK)

            drv.close()
            self.assertFalse(fcntl.fcntl(pipes.in_r, fcntl.F_GETFL) & os.O_NONBLOCK)
            self.assertFalse(fcntl.fcntl(pipes.out_w, fcntl.F_GETFL) & os.O_NONBLOCK)

        finally:
            pipes.close()

    def test_same_fd_for_both(self) -> None:
        # A socketpair end used as a plain fd works for both directions.
        import socket
        a, b = socket.socketpair()
        try:
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([UpperEchoIoPipelineHandler()]),
                a.fileno(),
                a.fileno(),
            )
            b.sendall(b'abc')
            self.assertIsInstance(_step(drv), Echoed)
            self.assertEqual(b.recv(100), b'ABC')
            drv.close()
        finally:
            a.close()
            b.close()

    def test_timeout(self) -> None:
        pipes = _Pipes()
        try:
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([UpperEchoIoPipelineHandler()]),
                pipes.in_r,
                pipes.out_w,
                timeout_s=.05,
            )
            with self.assertRaises(TimeoutError):
                drv.next()
        finally:
            pipes.close()

    def test_read_timeout_handler(self) -> None:
        pipes = _Pipes()
        try:
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([ReadTimeoutIoPipelineHandler(.05), UpperEchoIoPipelineHandler()]),
                pipes.in_r,
                pipes.out_w,
            )
            out = drv.next()
            self.assertIsInstance(out, TimeoutError)
        finally:
            pipes.close()

    def test_large_write_drains(self) -> None:
        # More than a pipe buffer's worth of output: the driver must not lose data when writes would block.
        pipes = _Pipes()
        try:
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([UpperEchoIoPipelineHandler()]),
                pipes.in_r,
                pipes.out_w,
            )
            payload = b'a' * (1 << 20)
            received = bytearray()

            def reader() -> None:
                while len(received) < len(payload):
                    chunk = os.read(pipes.out_r, 1 << 16)
                    if not chunk:
                        break
                    received.extend(chunk)

            t = threading.Thread(target=reader)
            t.start()

            def writer() -> None:
                view = memoryview(payload)
                while view:
                    n = os.write(pipes.in_w, view)
                    view = view[n:]
                os.close(pipes.in_w)

            wt = threading.Thread(target=writer)
            wt.start()

            while drv.is_running or drv.state is IoPipelineDriverState.NEW:
                out = drv.next(raise_on_stall=False)
                if out is not None:
                    self.assertIsInstance(out, Echoed)
            wt.join()
            os.close(pipes.out_w)
            t.join()
            self.assertEqual(bytes(received), payload.upper())
        finally:
            pipes.close()


##


class _Emit(IoPipelineMessages.AfterFinalInput):
    def __init__(self, *msgs: ta.Any) -> None:
        super().__init__()

        self.msgs = msgs


class _Received(IoPipelineMessages.AfterShutdownOutput):
    """Returned from next() after input is received, so a step can end while input remains open."""


class _HalfCloseIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.received = bytearray()
        self.saw_final_input = False
        self.errors: ta.List[BaseException] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for out_msg in msg.msgs:
                ctx.feed_out(out_msg)
            return

        if ByteStreamBuffers.can_bytes(msg):
            self.received.extend(ByteStreamBuffers.to_bytes(msg, strict=True))
            ctx.feed_out(_Received())
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True

        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return

        ctx.feed_in(msg)


def _read_until_eof(fd: int) -> bytes:
    out = bytearray()
    while (b := os.read(fd, 65536)):
        out.extend(b)
    return bytes(out)


class TestFdSyncIoPipelineDriverOutputShutdown(unittest.TestCase):
    def _capture_outcome(self, msg: IoPipelineMessages.Completable) -> ta.List[ta.Optional[BaseException]]:
        out: ta.List[ta.Optional[BaseException]] = []
        msg.add_listener(lambda m: out.append(m.get_exception() if m.is_failed() else None))
        return out

    def test_socket_write_fd_is_shut_down_without_closing_it(self) -> None:
        import socket

        sock, peer = socket.socketpair()
        try:
            app = _HalfCloseIoPipelineHandler()
            shutdown_output = IoPipelineMessages.ShutdownOutput()
            drv = FdSyncIoPipelineDriver(IoPipeline.Spec([app]), sock.fileno(), sock.fileno())
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_Emit(b'request', shutdown_output))
                self.assertIsNone(drv.next(read=False))

                self.assertTrue(shutdown_output.is_succeeded())
                self.assertTrue(drv.output_shutdown)
                peer.settimeout(5.)
                self.assertEqual(peer.recv(64), b'request')
                self.assertEqual(peer.recv(64), b'')

                # The caller's descriptor stays open, and the read half still works.
                os.fstat(sock.fileno())
                peer.sendall(b'response')
                peer.shutdown(socket.SHUT_WR)
                while not app.saw_final_input:
                    drv.next(raise_on_stall=False)
                self.assertEqual(bytes(app.received), b'response')
                self.assertEqual(app.errors, [])
            finally:
                drv.close()
            os.fstat(sock.fileno())
        finally:
            sock.close()
            peer.close()

    def test_caller_owned_pipe_fails_and_is_left_intact(self) -> None:
        pipes = _Pipes()
        try:
            app = _HalfCloseIoPipelineHandler()
            shutdown_output = IoPipelineMessages.ShutdownOutput()
            outcome = self._capture_outcome(shutdown_output)
            drv = FdSyncIoPipelineDriver(IoPipeline.Spec([app]), pipes.in_r, pipes.out_w)
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_Emit(b'request', shutdown_output))
                self.assertIsNone(drv.next(read=False))

                self.assertTrue(shutdown_output.is_failed())
                self.assertIsInstance(outcome[0], UnsupportedIoPipelineError)
                self.assertFalse(drv.output_shutdown)
                self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
                self.assertEqual(os.read(pipes.out_r, 64), b'request')

                # Still open: the test, as owner, can write to it.
                os.fstat(pipes.out_w)
                os.write(pipes.in_w, b'more input')
                self.assertIsInstance(drv.next(), _Received)
                self.assertEqual(bytes(app.received), b'more input')
            finally:
                drv.close()
        finally:
            pipes.close()

    def test_permitted_pipe_close_restores_flags_and_never_touches_a_reused_fd(self) -> None:
        pipes = _Pipes()
        reused: ta.List[int] = []
        try:
            out_w_flags = fcntl.fcntl(pipes.out_w, fcntl.F_GETFL)
            self.assertFalse(out_w_flags & os.O_NONBLOCK)
            # A duplicate shares the open file description, and with it the nonblocking flag.
            out_w_dup = os.dup(pipes.out_w)
            reused.append(out_w_dup)

            app = _HalfCloseIoPipelineHandler()
            shutdown_output = IoPipelineMessages.ShutdownOutput()
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([app]),
                pipes.in_r,
                pipes.out_w,
                close_write_fd_on_output_shutdown=True,
            )
            try:
                self.assertIsNone(drv.next(read=False))
                self.assertTrue(fcntl.fcntl(out_w_dup, fcntl.F_GETFL) & os.O_NONBLOCK)

                drv.enqueue(_Emit(b'request', shutdown_output))
                self.assertIsNone(drv.next(read=False))
                self.assertTrue(shutdown_output.is_succeeded())
                self.assertTrue(drv.output_shutdown)

                # Restored before closing, so the surviving duplicate is blocking again.
                self.assertFalse(fcntl.fcntl(out_w_dup, fcntl.F_GETFL) & os.O_NONBLOCK)
                with self.assertRaises(OSError):
                    os.fstat(pipes.out_w)

                # The duplicate keeps the pipe's write end alive; close it so the reader sees EOF.
                os.close(out_w_dup)
                reused.clear()
                self.assertEqual(_read_until_eof(pipes.out_r), b'request')

                # Whatever now occupies the closed descriptor number must not be touched by the driver.
                fresh_r, fresh_w = os.pipe()
                reused.extend((fresh_r, fresh_w))
                fresh_flags = {fd: fcntl.fcntl(fd, fcntl.F_GETFL) for fd in (fresh_r, fresh_w)}

                os.write(pipes.in_w, b'response')
                os.close(pipes.in_w)
                while not app.saw_final_input:
                    drv.next(raise_on_stall=False)
                self.assertEqual(bytes(app.received), b'response')
            finally:
                drv.close()

            for fd, flags in fresh_flags.items():
                self.assertEqual(fcntl.fcntl(fd, fcntl.F_GETFL), flags)
        finally:
            for fd in reused:
                try:
                    os.close(fd)
                except OSError:
                    pass
            pipes.close()

    def test_single_non_socket_fd_cannot_be_half_closed(self) -> None:
        master, slave = os.openpty()
        try:
            app = _HalfCloseIoPipelineHandler()
            shutdown_output = IoPipelineMessages.ShutdownOutput()
            outcome = self._capture_outcome(shutdown_output)
            drv = FdSyncIoPipelineDriver(
                IoPipeline.Spec([app]),
                slave,
                slave,
                close_write_fd_on_output_shutdown=True,
            )
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_Emit(shutdown_output))
                self.assertIsNone(drv.next(read=False))

                self.assertTrue(shutdown_output.is_failed())
                self.assertIsInstance(outcome[0], UnsupportedIoPipelineError)
                os.fstat(slave)
            finally:
                drv.close()
        finally:
            os.close(master)
            os.close(slave)
