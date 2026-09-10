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
