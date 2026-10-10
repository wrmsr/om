# ruff: noqa: UP006 UP007 UP037 UP041 UP045
# @om-lite
"""
Regression tests for defects found reviewing the half-close driver work. The ids in the comments (F1-F4, O1-O31, T1-T4)
are those of the review findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the defect as it
was found.
"""
import asyncio
import fcntl
import functools
import os
import pty
import resource
import socket
import threading
import time
import tty
import typing as ta
import unittest
import weakref

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ....streambufs.utils import ByteStreamBuffers
from ...asyncs import AsyncIoPipelineMessages
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import SawFinalOutputIoPipelineError
from ...errors import TimeoutIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...handlers.feedback import FeedbackInboundIoPipelineHandler
from ...multiplex.handlers import MultiplexIoPipelineHandler
from ...multiplex.tests.apps import app_spec
from ...multiplex.tests.loopback import LoopbackAdapter
from ...multiplex.tests.loopback import LOpen
from ...multiplex.tests.loopback import LReset
from ...sched.timeouts import WriteTimeoutIoPipelineHandler
from ...ssl.tests.test_halfclose import _App
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..pure import PureIoPipelineDriver
from ..sync import FdSyncIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver
from ..sync import SyncIoPipelineDriver
from ..types import IoPipelineDriverState


##


def _is_nonblocking(fd: int) -> bool:
    return bool(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_NONBLOCK)


class _CloseAtOnce(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_final_output()
            return

        ctx.feed_in(msg)


class TestFdSyncSharedOpenFileDescription(unittest.TestCase):
    # The nonblocking flag lives on the open file description. When the read and write descriptors are dups of one
    # description - a process's stdin and stdout on the same terminal, typically - the driver must restore the
    # description to its original mode, not leave the terminal nonblocking for whatever runs next.

    def _run(self, read_fd: int, write_fd: int) -> None:
        d = FdSyncIoPipelineDriver(IoPipeline.Spec([_CloseAtOnce()]), read_fd, write_fd)
        d.loop_until_done()

    def test_dup_pair_restored_to_blocking(self) -> None:
        a, b = socket.socketpair()
        try:
            r = a.fileno()
            w = os.dup(r)
            try:
                self.assertFalse(_is_nonblocking(r))
                self.assertFalse(_is_nonblocking(w))

                self._run(r, w)

                self.assertFalse(_is_nonblocking(r))
                self.assertFalse(_is_nonblocking(w))
            finally:
                os.close(w)
        finally:
            a.close()
            b.close()

    def test_dup_pair_restored_to_blocking_with_higher_read_fd(self) -> None:
        # The order in which the two descriptors are visited must not matter.
        a, b = socket.socketpair()
        try:
            w = a.fileno()
            r = os.dup(w)
            try:
                self._run(r, w)

                self.assertFalse(_is_nonblocking(r))
                self.assertFalse(_is_nonblocking(w))
            finally:
                os.close(r)
        finally:
            a.close()
            b.close()

    def test_originally_nonblocking_description_stays_nonblocking(self) -> None:
        a, b = socket.socketpair()
        try:
            a.setblocking(False)
            r = a.fileno()
            w = os.dup(r)
            try:
                self._run(r, w)

                self.assertTrue(_is_nonblocking(r))
                self.assertTrue(_is_nonblocking(w))
            finally:
                os.close(w)
        finally:
            a.close()
            b.close()


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


class TestDuplicateFinalOutputPerDriver(unittest.TestCase):
    # F1 from reviewer 3's angle: before the fix, the second FinalOutput reached each driver, which crashed on a bare
    # `check.none`. Now the terminal rejects it, so every driver sees exactly one; the application is told of its
    # mistake by an inbound Error.

    def _check(self, app: _DupFinalApp) -> None:
        self.assertTrue(app.second.is_failed())
        (exc,) = app.errors
        self.assertIsInstance(exc, SawFinalOutputIoPipelineError)

    def test_pure_driver_duplicate_final_output(self) -> None:
        app = _DupFinalApp()
        driver = PureIoPipelineDriver(IoPipeline.Spec([app], services=[StubIoPipelineFlowService()]))
        try:
            driver.next(raise_on_stall=False)
            self._check(app)
            driver.drain_output()
            self.assertTrue(app.first.is_succeeded())
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
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
                self._check(app)
                self.assertTrue(app.first.is_succeeded())
                self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
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
                self.assertIsNone(driver.next(read=False))
                self._check(app)
                self.assertTrue(app.first.is_succeeded())
                self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
            finally:
                driver.close()
        finally:
            peer.close()


class _FencedOutput(IoPipelineHandler):
    """Writes, flushes, half-closes and closes on InitialInput, recording each fence's outcome from its listener."""

    def __init__(self) -> None:
        super().__init__()

        self.flush = IoPipelineFlowMessages.FlushOutput()
        self.shutdown = IoPipelineMessages.ShutdownOutput()
        self.final = IoPipelineMessages.FinalOutput()
        self.outcomes: ta.List[ta.Tuple[str, ta.Optional[BaseException]]] = []
        for name, fence in (('flush', self.flush), ('shutdown', self.shutdown), ('final', self.final)):
            fence.add_listener(functools.partial(self._on_done, name))

    def _on_done(self, name: str, msg: IoPipelineMessages.Completable) -> None:
        self.outcomes.append((name, msg.get_exception() if msg.is_failed() else None))

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(b'payload')
            ctx.feed_out(self.flush)
            ctx.feed_out(self.shutdown)
            ctx.feed_out(self.final)
            return

        ctx.feed_in(msg)


class TestPureFailOutput(unittest.TestCase):
    # T2 (TODO.md: "let the pure driver simulate write failures once its peer is gone"). `fail_output()` makes the next
    # drain step behave as a socket driver's write does once the peer has gone: the queued fences and a held
    # FinalOutput fail, in order, the driver fails, and the error is raised from the step.

    def test_queued_fences_fail_in_order(self) -> None:
        app = _FencedOutput()
        driver = PureIoPipelineDriver(IoPipeline.Spec([app], services=[StubIoPipelineFlowService()]))
        try:
            self.assertIsNone(driver.next(read=False))
            self.assertTrue(driver.has_pending_output)
            exc = BrokenPipeError('peer closed')
            driver.fail_output(exc)
            with self.assertRaises(BrokenPipeError) as raised:
                driver.drain_output()
            self.assertIs(raised.exception, exc)
            self.assertEqual([name for name, _ in app.outcomes], ['flush', 'shutdown', 'final'])
            self.assertTrue(all(e is exc for _, e in app.outcomes))
            self.assertIs(driver.state, IoPipelineDriverState.FAILED)
            self.assertFalse(driver.pipeline.is_ready)
        finally:
            driver.close()

    def test_failure_with_nothing_queued_still_fails_the_next_step(self) -> None:
        driver = PureIoPipelineDriver(IoPipeline.Spec(services=[StubIoPipelineFlowService()]))
        try:
            self.assertIsNone(driver.next(read=False))
            self.assertFalse(driver.has_pending_output)
            driver.fail_output(ConnectionResetError('reset'))
            self.assertTrue(driver.has_pending_output)
            with self.assertRaises(ConnectionResetError):
                driver.drain_output()
            self.assertIs(driver.state, IoPipelineDriverState.FAILED)
        finally:
            driver.close()


class TestFdSyncSharedOpenFileDescriptionAfterClose(unittest.TestCase):
    # F2 from reviewer 2's angle (their IO-03): dups of one socket as read and write descriptors, closed abortively
    # or after a graceful FinalOutput, and a dup of a PTY slave through the permitted write-descriptor close.

    def test_duplicate_socket_descriptors_restore_original_flags(self) -> None:
        for graceful in (False, True):
            with self.subTest(graceful=graceful):
                sock, peer = socket.socketpair()
                read_fd = os.dup(sock.fileno())
                write_fd = os.dup(sock.fileno())
                original = fcntl.fcntl(read_fd, fcntl.F_GETFL)
                feedback = FeedbackInboundIoPipelineHandler()
                driver = FdSyncIoPipelineDriver(
                    IoPipeline.Spec([feedback], services=[StubIoPipelineFlowService(auto_read=False)]),
                    read_fd,
                    write_fd,
                )
                try:
                    driver.next(read=False)
                    self.assertTrue(fcntl.fcntl(read_fd, fcntl.F_GETFL) & os.O_NONBLOCK)
                    if graceful:
                        final = IoPipelineMessages.FinalOutput()
                        driver.enqueue(feedback.wrap(final))
                        driver.next(read=False)
                        self.assertTrue(final.is_succeeded())
                    driver.close()
                    self.assertEqual(fcntl.fcntl(read_fd, fcntl.F_GETFL), original)
                    self.assertEqual(fcntl.fcntl(write_fd, fcntl.F_GETFL), original)
                finally:
                    driver.close()
                    os.close(read_fd)
                    os.close(write_fd)
                    sock.close()
                    peer.close()

    def test_terminal_read_descriptor_restores_flags_after_write_half_close(self) -> None:
        master, write_fd = pty.openpty()
        tty.setraw(write_fd)
        read_fd = os.dup(write_fd)
        original = fcntl.fcntl(read_fd, fcntl.F_GETFL)
        feedback = FeedbackInboundIoPipelineHandler()
        driver = FdSyncIoPipelineDriver(
            IoPipeline.Spec([feedback], services=[StubIoPipelineFlowService(auto_read=False)]),
            read_fd,
            write_fd,
            close_write_fd_on_output_shutdown=True,
        )
        shutdown = IoPipelineMessages.ShutdownOutput()
        try:
            driver.next(read=False)
            driver.enqueue(feedback.wrap(shutdown))
            driver.next(read=False)
            self.assertTrue(shutdown.is_succeeded())
            self.assertTrue(fcntl.fcntl(read_fd, fcntl.F_GETFL) & os.O_NONBLOCK)
            driver.close()
            self.assertEqual(fcntl.fcntl(read_fd, fcntl.F_GETFL), original)
        finally:
            driver.close()
            if not shutdown.is_succeeded():
                os.close(write_fd)
            os.close(read_fd)
            os.close(master)


class _SendAndFinishMegabyte(IoPipelineHandler):
    """Writes 1 MiB on InitialInput and then FinalOutput, never reading."""

    def __init__(self) -> None:
        super().__init__()

        self.final = IoPipelineMessages.FinalOutput()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(b'x' * (1024 * 1024))
            ctx.feed_out(self.final)
        else:
            ctx.feed_in(msg)


class TestFdioFinalDrainAgainstSendingPeer(unittest.TestCase):
    # The passing control for O1 (reviewer 2's IO-01): the fdio driver keeps reading, and discarding, while draining,
    # so a raw peer which sends a megabyte before reading does not stall it.

    def test_final_drain_keeps_receiving(self) -> None:
        socks = socket.socketpair()
        for sock in socks:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        app = _SendAndFinishMegabyte()
        poller = SelectFdioPoller()
        manager = FdioManager(poller)
        driver = IoPipelineDriverSocketFdioHandler(
            socks[0],
            ('local', 0),
            IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=False)]),
        )
        socks[1].settimeout(5.)
        errors: ta.List[BaseException] = []

        def peer() -> None:
            try:
                socks[1].sendall(b'y' * (1024 * 1024))
                received = bytearray()
                while len(received) < 1024 * 1024:
                    chunk = socks[1].recv(65536)
                    if not chunk:
                        break
                    received.extend(chunk)
                if received != b'x' * (1024 * 1024):
                    raise AssertionError(f'peer received only {len(received)} bytes')
            except BaseException as exc:  # noqa
                errors.append(exc)

        thread = threading.Thread(target=peer, daemon=True)
        try:
            thread.start()
            self.assertIsNone(driver.next(read=False))
            manager.register(driver)
            deadline = time.monotonic() + 5.
            while driver.is_active:
                self.assertLess(time.monotonic(), deadline)
                manager.poll(timeout=.1)
            thread.join(5.)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
            self.assertTrue(app.final.is_succeeded())
        finally:
            driver.close()
            poller.close()
            socks[1].close()
            thread.join(5.)


##


class _SendAllThenFinish(IoPipelineHandler):
    """Writes its whole payload on InitialInput, then FinalOutput, and never reads."""

    def __init__(self, payload: bytes) -> None:
        super().__init__()

        self._payload = payload
        self.final_output = IoPipelineMessages.FinalOutput()
        self.received = 0

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            mv = memoryview(self._payload)
            for pos in range(0, len(mv), 64 * 1024):
                ctx.feed_out(mv[pos:pos + 64 * 1024])
            ctx.feed_out(self.final_output)
            return

        if ByteStreamBuffers.can_bytes(msg):
            self.received += len(ByteStreamBuffers.to_bytes(msg, strict=True))
            return

        ctx.feed_in(msg)


_PAYLOAD = b'x' * (4 * 1024 * 1024)


class TestDrainingDuplexDeadlock(unittest.TestCase):
    # O1. DESIGN 8: "While draining after FinalOutput, the pure and fdio drivers keep taking input off the transport
    # and discard it: nothing consumes it any more, but a peer whose own output waits for this side to read must not
    # wait forever." The sync driver does not: once it holds a FinalOutput it only waits for writability, so two such
    # peers, each with more queued than the socket buffers hold, wait on each other forever. The fdio driver's
    # equivalent (`test_driver_edges.TestDrainingDuplexDeadlock`) passes.

    def test_sync_both_draining(self) -> None:
        ha, hb = _SendAllThenFinish(_PAYLOAD), _SendAllThenFinish(_PAYLOAD)
        sa, sb = socket.socketpair()
        da = SocketSyncIoPipelineDriver(IoPipeline.Spec([ha]), sa)
        db = SocketSyncIoPipelineDriver(IoPipeline.Spec([hb]), sb)
        # Bounds the wait so a deadlock surfaces as a TimeoutError rather than a hung test.
        da.wait_timeout_s = db.wait_timeout_s = 3.

        errors: ta.Dict[str, BaseException] = {}

        def run(name: str, d: SocketSyncIoPipelineDriver, sock: socket.socket) -> None:
            try:
                d.loop_until_done()
            except BaseException as e:  # noqa
                errors[name] = e
            finally:
                # The socket is the caller's: done with it, the caller closes it, as a real peer would.
                sock.close()

        threads = [
            threading.Thread(target=run, args=('a', da, sa), daemon=True),
            threading.Thread(target=run, args=('b', db, sb), daemon=True),
        ]
        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=15.)
            self.assertFalse(any(t.is_alive() for t in threads))

            for name in ('a', 'b'):
                self.assertNotIsInstance(errors.get(name), TimeoutError, f'{name} deadlocked: {errors.get(name)!r}')

            # One side drained everything - its peer kept reading while draining - and closed; the other's remaining
            # output then has no reader, which fails it.
            self.assertTrue(ha.final_output.is_succeeded() or hb.final_output.is_succeeded())
            for d, h in ((da, ha), (db, hb)):
                if not h.final_output.is_succeeded():
                    self.assertIs(d.state, IoPipelineDriverState.FAILED)
        finally:
            da.close()
            db.close()
            sa.close()
            sb.close()


class TestDrainingDuplexDeadlockAsyncio(AsyncioIsolatedAsyncTestCase):
    # O1. The asyncio driver cancels its read task on FinalOutput and then waits for the writer to close - which
    # waits for the transport to flush, which waits for the peer to read. The transport itself stops reading once the
    # stream reader's buffer is full, so two such peers deadlock just like the sync ones.

    async def test_asyncio_both_draining(self) -> None:
        ha, hb = _SendAllThenFinish(_PAYLOAD), _SendAllThenFinish(_PAYLOAD)
        sa, sb = socket.socketpair()
        try:
            ra, wa = await asyncio.open_connection(sock=sa)
            rb, wb = await asyncio.open_connection(sock=sb)
            da = PollAsyncioStreamIoPipelineDriver(IoPipeline.Spec([ha]), ra, wa)
            db = PollAsyncioStreamIoPipelineDriver(IoPipeline.Spec([hb]), rb, wb)
            try:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(da.loop_until_done(), db.loop_until_done(), return_exceptions=True),
                        5.,
                    )
                except asyncio.TimeoutError:
                    self.fail(f'both drivers deadlocked while draining: {da.state}, {db.state}')
            finally:
                await da.close()
                await db.close()

            self.assertTrue(ha.final_output.is_succeeded() or hb.final_output.is_succeeded())
            for d, h in ((da, ha), (db, hb)):
                if not h.final_output.is_succeeded():
                    self.assertIs(d.state, IoPipelineDriverState.FAILED)
        finally:
            sa.close()
            sb.close()


##


class _SendAndEndOutput(IoPipelineHandler):
    """Writes 1 MiB on InitialInput and then ends its output with `final` (FinalOutput unless replaced)."""

    def __init__(self) -> None:
        super().__init__()

        self.final: ta.Union[IoPipelineMessages.FinalOutput, IoPipelineMessages.ShutdownOutput] = (
            IoPipelineMessages.FinalOutput()
        )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(b'x' * (1024 * 1024))
            ctx.feed_out(self.final)
        else:
            ctx.feed_in(msg)


def _spec(app: IoPipelineHandler) -> IoPipeline.Spec:
    # The application needs no more input. Draining its final output must still free transport space for the peer.
    return IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=False)])


def _small_sockets() -> ta.Tuple[socket.socket, socket.socket]:
    pair = socket.socketpair()
    for sock in pair:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    return pair


def _peer(sock: socket.socket, errors: ta.List[BaseException]) -> None:
    """A raw peer which sends its own megabyte first and only then reads the driver's."""

    try:
        sock.sendall(b'y' * (1024 * 1024))
        received = bytearray()
        while len(received) < 1024 * 1024:
            chunk = sock.recv(65536)
            if not chunk:
                break
            received.extend(chunk)
        if received != b'x' * (1024 * 1024):
            raise AssertionError(f'peer received only {len(received)} bytes')
    except BaseException as exc:  # noqa
        errors.append(exc)


class TestSyncFinalDrainAgainstSendingPeer(unittest.TestCase):
    # O1 from reviewer 2's angle (their IO-01): the peer is a raw socket which sends a megabyte before it reads. With
    # small socket buffers the driver's drain cannot progress until the peer's send does, which needs the driver to
    # keep reading.

    def _run(self, *, fd: bool) -> None:
        socks = _small_sockets()
        app = _SendAndEndOutput()
        for sock in socks:
            sock.settimeout(2.)
        driver: SyncIoPipelineDriver
        if fd:
            driver = FdSyncIoPipelineDriver(_spec(app), socks[0].fileno(), socks[0].fileno(), timeout_s=2.)
        else:
            driver = SocketSyncIoPipelineDriver(_spec(app), socks[0])
        errors: ta.List[BaseException] = []
        thread = threading.Thread(target=_peer, args=(socks[1], errors), daemon=True)
        try:
            thread.start()
            driver.loop_until_done()
            thread.join(5.)
            self.assertFalse(thread.is_alive())
            self.assertEqual(errors, [])
            self.assertTrue(app.final.is_succeeded())
        finally:
            driver.close()
            for sock in socks:
                sock.close()
            thread.join(5.)

    def test_socket_final_drain_keeps_receiving(self) -> None:
        self._run(fd=False)

    def test_fd_final_drain_keeps_receiving(self) -> None:
        self._run(fd=True)


class TestAsyncioFinalDrain(AsyncioIsolatedAsyncTestCase):
    # O1 (reviewer 2's IO-01), asyncio: the stream reader's limit is tiny, so the transport pauses reading as soon as
    # the driver stops consuming, and the peer's send never completes.

    async def test_final_drain_keeps_receiving(self) -> None:
        socks = _small_sockets()
        app = _SendAndEndOutput()
        reader, writer = await asyncio.open_connection(sock=socks[0], limit=4096)
        driver = PollAsyncioStreamIoPipelineDriver(_spec(app), reader, writer)
        socks[1].setblocking(False)

        async def peer() -> None:
            loop = asyncio.get_running_loop()
            await loop.sock_sendall(socks[1], b'y' * (1024 * 1024))
            received = bytearray()
            while len(received) < 1024 * 1024:
                chunk = await loop.sock_recv(socks[1], 65536)
                if not chunk:
                    break
                received.extend(chunk)
            self.assertEqual(received, b'x' * (1024 * 1024))

        work = asyncio.gather(driver.loop_until_done(), peer())
        try:
            await asyncio.wait_for(work, 2.)
            self.assertTrue(app.final.is_succeeded())
        finally:
            work.cancel()
            await asyncio.gather(work, return_exceptions=True)
            await driver.close()
            for sock in socks:
                sock.close()

    # O17 (reviewer 2's IO-02, and TODO.md's "decide whether asyncio ShutdownOutput should complete only once the FIN
    # is actually sent"). `write_eof()` defers the socket's half-close until the transport buffer is empty, but the
    # fence completes after an ordinary `drain()`, which returns at the low watermark - here with a megabyte still
    # buffered and no FIN sent. DESIGN 5: success means the transport's output half was shut down.

    async def test_shutdown_completion_waits_for_transport_half_close(self) -> None:
        socks = _small_sockets()
        app = _SendAndEndOutput()
        app.final = IoPipelineMessages.ShutdownOutput()
        done = asyncio.Event()
        buffered_at_completion: ta.List[int] = []
        reader, writer = await asyncio.open_connection(sock=socks[0])

        def on_done(msg: ta.Any) -> None:
            buffered_at_completion.append(writer.transport.get_write_buffer_size())
            done.set()

        app.final.add_listener(on_done)
        # Watermarks above the payload: an ordinary drain would return at once, with everything still buffered.
        driver = PollAsyncioStreamIoPipelineDriver(
            _spec(app),
            reader,
            writer,
            config=PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=2 * 1024 * 1024,
                write_low_watermark=1024 * 1024,
            ),
        )
        socks[1].setblocking(False)

        async def peer() -> bytes:
            # Reads everything the driver sends, up to the EOF its half-close produces.
            loop = asyncio.get_running_loop()
            received = bytearray()
            while True:
                chunk = await loop.sock_recv(socks[1], 65536)
                if not chunk:
                    return bytes(received)
                received.extend(chunk)

        task = asyncio.create_task(driver.loop_until_done())
        try:
            received = await asyncio.wait_for(peer(), 5.)
            self.assertEqual(len(received), 1024 * 1024)  # The EOF followed the whole payload: the FIN was sent.
            await asyncio.wait_for(done.wait(), 2.)
            self.assertTrue(app.final.is_succeeded())
            self.assertEqual(buffered_at_completion, [0])  # Nothing was still buffered when the fence completed.
        finally:
            await driver.close()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            for sock in socks:
                sock.close()


##


class _SendAllThenFinishAndReport(_SendAllThenFinish):
    """As _SendAllThenFinish, additionally handing inbound errors to a callback."""

    def __init__(self, payload: bytes, on_error: ta.Callable[[BaseException], None]) -> None:
        super().__init__(payload)

        self._on_error = on_error

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self._on_error(msg.exc)
            return

        super().inbound(ctx, msg)


class TestAsyncioTimersDuringGracefulClose(AsyncioIsolatedAsyncTestCase):
    # O8. DESIGN 7: scheduled callbacks run inside the owning pipeline; DESIGN 8: a driver integrates scheduler
    # deadlines. The asyncio driver handles FinalOutput by awaiting the writer's graceful close inside its command
    # loop, so while a peer which has stopped reading keeps that close from completing, no command - and so no timer,
    # including a WriteTimeoutIoPipelineHandler's - runs. The sync and fdio drivers keep running timers while they
    # wait to write.

    async def test_write_timeout_fires_while_final_output_drains(self) -> None:
        timed_out: asyncio.Future = asyncio.get_running_loop().create_future()

        def on_error(exc: BaseException) -> None:
            if not timed_out.done():
                timed_out.set_result(exc)

        sa, sb = socket.socketpair()  # sb never reads
        try:
            reader, writer = await asyncio.open_connection(sock=sa)
            app = _SendAllThenFinishAndReport(_PAYLOAD, on_error)
            d = PollAsyncioStreamIoPipelineDriver(
                IoPipeline.Spec([WriteTimeoutIoPipelineHandler(.3), app]),
                reader,
                writer,
            )
            task = asyncio.create_task(d.loop_until_done())
            try:
                try:
                    exc = await asyncio.wait_for(timed_out, 3.)
                except asyncio.TimeoutError:
                    self.fail(f'no write timeout was delivered while draining: {d.state}')
                self.assertIsInstance(exc, TimeoutIoPipelineError)
            finally:
                await d.close()
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        finally:
            sa.close()
            sb.close()


##


class TestSelectDescriptorLimit(unittest.TestCase):
    # O18 (reviewer 2's IO-04). Both synchronous drivers wait with `select.select()`, whose descriptor-number limit
    # (FD_SETSIZE, 1024 here and on darwin) is below the process's valid descriptor range: a perfectly good socket
    # numbered 1024 fails them with `ValueError: filedescriptor out of range in select()`.

    def test_valid_high_numbered_descriptors_transfer_and_half_close(self) -> None:
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        if soft_limit != resource.RLIM_INFINITY and soft_limit <= 1024:
            self.skipTest('process descriptor limit does not permit a descriptor above FD_SETSIZE')
        for fd in (False, True):
            for high in (False, True):
                with self.subTest(fd=fd, high=high):
                    sock, peer = socket.socketpair()
                    transport = socket.socket(fileno=fcntl.fcntl(sock.fileno(), fcntl.F_DUPFD, 1024)) if high else sock
                    transport.settimeout(2.)
                    peer.settimeout(2.)
                    app = _App(respond=b'response')
                    spec = IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=True)])
                    driver: SyncIoPipelineDriver
                    if fd:
                        driver = FdSyncIoPipelineDriver(spec, transport.fileno(), transport.fileno(), timeout_s=2.)
                    else:
                        driver = SocketSyncIoPipelineDriver(spec, transport)
                    try:
                        peer.sendall(b'request')
                        peer.shutdown(socket.SHUT_WR)
                        driver.loop_until_done()
                        self.assertEqual(bytes(app.received), b'request')
                        received = bytearray()
                        while chunk := peer.recv(128):
                            received.extend(chunk)
                        self.assertEqual(received, b'response')
                        self.assertTrue(app.shutdown_output.is_succeeded())
                        self.assertTrue(app.final_output.is_succeeded())
                    finally:
                        driver.close()
                        transport.close()
                        sock.close()
                        peer.close()


##


class _Payload:
    pass


class _AwaitApp(IoPipelineHandler):
    """Sends an Await of a coroutine which blocks until released, on InitialInput."""

    def __init__(self) -> None:
        super().__init__()

        self.started = asyncio.Event()
        self.blocker = asyncio.Event()
        self.task: ta.Optional[asyncio.Task] = None
        self.await_message: ta.Optional[AsyncIoPipelineMessages.Await] = None

    async def run(self) -> None:
        self.task = asyncio.current_task()
        self.started.set()
        await self.blocker.wait()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self.await_message = AsyncIoPipelineMessages.Await(self.run())
            ctx.feed_out(self.await_message)
        if not isinstance(msg, IoPipelineMessages.Error):
            ctx.feed_in(msg)


class TestAsyncioLifecycle(AsyncioIsolatedAsyncTestCase):
    # O19-O23 (reviewer 2's IO-05 to IO-09): what the asyncio driver's `close()` leaves behind, and what a cancelled
    # waiter does to it. The first test runs every driver; only the pure driver passes it.

    async def test_close_releases_unprocessed_input(self) -> None:
        # O23 (IO-09). Input enqueued before the first step is retained by a closed driver's queue.
        for kind in ('pure', 'socket', 'fd', 'fdio', 'asyncio'):
            with self.subTest(driver=kind):
                sock, peer = socket.socketpair()
                spec = IoPipeline.Spec(services=[StubIoPipelineFlowService(auto_read=False)])
                driver: ta.Any
                if kind == 'pure':
                    driver = PureIoPipelineDriver(spec)
                elif kind == 'socket':
                    driver = SocketSyncIoPipelineDriver(spec, sock)
                elif kind == 'fd':
                    driver = FdSyncIoPipelineDriver(spec, sock.fileno(), sock.fileno())
                elif kind == 'fdio':
                    driver = IoPipelineDriverSocketFdioHandler(sock, ('local', 0), spec)
                else:
                    reader, writer = await asyncio.open_connection(sock=sock)
                    driver = PollAsyncioStreamIoPipelineDriver(spec, reader, writer)
                try:
                    payload = _Payload()
                    ref = weakref.ref(payload)
                    driver.enqueue(payload)
                    del payload
                    if kind == 'asyncio':
                        await driver.close()
                    else:
                        driver.close()
                    self.assertIsNone(ref(), 'closed driver retained input which can never be processed')
                finally:
                    if kind == 'asyncio':
                        await driver.close()
                    else:
                        driver.close()
                    sock.close()
                    peer.close()

    async def _driver(self, *handlers: IoPipelineHandler) -> PollAsyncioStreamIoPipelineDriver:
        sock, peer = socket.socketpair()
        self.addCleanup(peer.close)
        self.addCleanup(sock.close)
        reader, writer = await asyncio.open_connection(sock=sock)
        return PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(handlers, services=[StubIoPipelineFlowService(auto_read=False)]),
            reader,
            writer,
        )

    async def test_close_finishes_unprocessed_enqueue_waitable(self) -> None:
        # O21 (IO-07). A waiter for a command the closed driver never processed waits forever.
        driver = await self._driver()
        pending = driver.enqueue_waitable()
        try:
            await driver.close()
            self.assertTrue(pending.done(), 'an enqueue waiter can now wait forever on the closed driver')
            if not pending.cancelled():
                self.assertIsNotNone(pending.exception())
        finally:
            pending.cancel()
            await driver.close()

    async def test_cancelled_enqueue_waiter_does_not_fail_driver(self) -> None:
        # O22 (IO-08). `set_result` on the cancelled waiter raises InvalidStateError and fails the driver.
        driver = await self._driver()
        try:
            pending = driver.enqueue_waitable()
            pending.cancel()
            self.assertIsNone(await driver.next(read=False))
            self.assertTrue(driver.pipeline.is_ready)
        finally:
            await driver.close()

    async def test_close_cancels_a_coroutine_started_by_await(self) -> None:
        # O19 (IO-05, and TODO.md's "clear the asyncio driver's _pending_awaits on close()"). The driver created the
        # task for the Await's coroutine; closing fails the Await but leaves the task running.
        app = _AwaitApp()
        driver = await self._driver(app)
        try:
            self.assertIsNone(await driver.next(read=False))
            await asyncio.wait_for(app.started.wait(), 2.)
            await driver.close()
            assert app.await_message is not None
            assert app.task is not None
            self.assertTrue(app.await_message.is_failed())
            self.assertTrue(app.task.done(), 'the closed driver left its application coroutine running')
        finally:
            await driver.close()
            if app.task is not None:
                app.task.cancel()
                await asyncio.gather(app.task, return_exceptions=True)

    async def test_reset_cancels_a_coroutine_started_by_child_await(self) -> None:
        # O20 (IO-06). A child's Await is forwarded to the parent driver; resetting the stream fails the child's
        # message and removes the stream, but the coroutine runs on in the parent.
        app = _AwaitApp()
        mux = MultiplexIoPipelineHandler(LoopbackAdapter(), lambda opening: app_spec(app))
        driver = await self._driver(mux)
        try:
            driver.enqueue(LOpen('k'))
            while await driver.next(read=False) is not None:
                pass
            await asyncio.wait_for(app.started.wait(), 2.)

            driver.enqueue(LReset('k'))
            while await driver.next(read=False) is not None:
                pass
            await asyncio.sleep(0)  # Let task cancellation be delivered, if the child requested it.
            assert app.await_message is not None
            assert app.task is not None
            self.assertTrue(app.await_message.is_failed())
            self.assertTrue(driver.pipeline.is_ready)
            self.assertNotIn('k', mux.streams)
            self.assertTrue(app.task.done(), 'the reset stream left its application coroutine running')
        finally:
            await driver.close()
            if app.task is not None:
                app.task.cancel()
                await asyncio.gather(app.task, return_exceptions=True)
