# ruff: noqa: SLF001 UP006 UP037 UP045
import fcntl
import os
import pty
import socket
import threading
import time
import tty
import typing as ta
import unittest
import weakref

from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...drivers.types import IoPipelineDriverState
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..pure import PureIoPipelineDriver
from ..sync import FdSyncIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver


class _Emit:
    def __init__(self, *msgs: ta.Any) -> None:
        self.msgs = msgs


class _Recorder(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []
        self.writability_after_shutdown: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for m in msg.msgs:
                ctx.feed_out(m)
            return

        self.inputs.append(msg)
        # Matches test_pure's test_writability_is_not_announced_after_shutdown: the PauseOutput for bytes queued ahead
        # of the fence is fine, but no ReadyForOutput may follow once ShutdownOutput reached the terminal.
        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput) and ctx.pipeline.saw_shutdown_output:
            self.writability_after_shutdown.append(msg)

        if ByteStreamBuffers.can_bytes(msg):
            return
        ctx.feed_in(msg)


def _spec(h: IoPipelineHandler) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [h],
        IoPipeline.Config(inbound_terminal='drop'),
        services=[StubIoPipelineFlowService()],
    )


class TestWritabilityAfterShutdownOutput(unittest.TestCase):
    # DESIGN 6: "Once output has been shut down, no further transitions are announced: nothing may produce ordinary
    # output." The terminal rejects ordinary output as soon as ShutdownOutput reaches it, yet the drivers gate
    # announcements on the *transport* shutdown, so a ReadyForOutput is announced in between.

    def test_pure_partial_drain(self) -> None:
        h = _Recorder()
        so = IoPipelineMessages.ShutdownOutput()
        drv = PureIoPipelineDriver(_spec(h), PureIoPipelineDriver.Config(write_high_watermark=4, write_low_watermark=2))
        try:
            assert drv.next(read=False) is None
            drv.enqueue(_Emit(b'abcdef', so))
            assert drv.next(read=False) is None
            assert drv.pipeline.saw_shutdown_output

            assert drv.drain_output(4) == b'abcd'
            assert not so.is_done()

            assert h.writability_after_shutdown == []
        finally:
            drv.close()

    def test_sync_chunked_drain(self) -> None:
        h = _Recorder()
        so = IoPipelineMessages.ShutdownOutput()
        a, b = socket.socketpair()
        try:
            drv = SocketSyncIoPipelineDriver(
                _spec(h),
                a,
                SocketSyncIoPipelineDriver.Config(
                    write_high_watermark=4,
                    write_low_watermark=2,
                    write_chunk_max=2,
                ),
            )
            try:
                assert drv.next(read=False) is None
                drv.enqueue(_Emit(b'abcdef', so))
                assert drv.next(read=False) is None
                assert so.is_succeeded()

                assert h.writability_after_shutdown == []
            finally:
                drv.close()
        finally:
            a.close()
            b.close()


class _EchoUnhandled(_Recorder):
    """Returns each input byte buffer to the driver's caller as unhandled output so `next()` returns."""

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        super().inbound(ctx, msg)
        if ByteStreamBuffers.can_bytes(msg):
            ctx.feed_out(_Observed(ByteStreamBuffers.to_bytes(msg, strict=True)))


class _Observed(IoPipelineMessages.AfterShutdownOutput):
    def __init__(self, data: bytes) -> None:
        super().__init__()

        self.data = data


class TestFdSyncSharedOpenFileDescription(unittest.TestCase):
    # FdSyncIoPipelineDriver's permitted close-on-shutdown restores the write fd's original flags before closing it.
    # O_NONBLOCK lives on the open file description: when the read fd shares it (stdin/stdout on a terminal are usually
    # dups of one open tty), the driver's still-active read fd silently becomes blocking. Whether it happens depends on
    # the iteration order of `{read_fd, write_fd}` in `_prepare_transport`: here write_fd < read_fd.

    def _fds(self) -> ta.Tuple[int, int, int]:
        master, slave = pty.openpty()
        tty.setraw(slave)
        read_fd = os.dup(slave)
        return master, read_fd, slave

    def test_read_fd_stays_nonblocking_after_permitted_close(self) -> None:
        master, read_fd, write_fd = self._fds()
        h = _Recorder()
        so = IoPipelineMessages.ShutdownOutput()
        try:
            drv = FdSyncIoPipelineDriver(
                _spec(h),
                read_fd,
                write_fd,
                close_write_fd_on_output_shutdown=True,
            )
            try:
                assert drv.next(read=False) is None
                assert fcntl.fcntl(read_fd, fcntl.F_GETFL) & os.O_NONBLOCK

                drv.enqueue(_Emit(b'x', so))
                assert drv.next(read=False) is None
                assert so.is_succeeded(), so

                # The driver is still running and reading from read_fd.
                assert drv.pipeline.is_ready
                assert fcntl.fcntl(read_fd, fcntl.F_GETFL) & os.O_NONBLOCK
            finally:
                drv.close()
        finally:
            os.close(master)
            os.close(read_fd)

    def test_read_after_permitted_close_does_not_hang(self) -> None:
        master, read_fd, write_fd = self._fds()
        h = _EchoUnhandled()
        so = IoPipelineMessages.ShutdownOutput()
        drv = FdSyncIoPipelineDriver(
            _spec(h),
            read_fd,
            write_fd,
            FdSyncIoPipelineDriver.Config(read_chunk_size=4, read_batch_max_reads=2),
            close_write_fd_on_output_shutdown=True,
        )
        done = threading.Event()
        result: ta.List[ta.Any] = []
        try:
            assert drv.next(read=False) is None
            drv.enqueue(_Emit(b'x', so))
            assert drv.next(read=False) is None
            assert so.is_succeeded(), so

            os.write(master, b'abcd')

            def run() -> None:
                try:
                    result.append(drv.next(read=True, raise_on_stall=False))
                finally:
                    done.set()

            t = threading.Thread(target=run, daemon=True)
            t.start()
            finished = done.wait(2.)
            if not finished:
                # Unblock the reader so the thread can exit.
                os.write(master, b'zzzz')
                assert done.wait(2.)
            assert finished, 'driver read blocked on a descriptor it believes is nonblocking'
            assert isinstance(result[0], _Observed) and result[0].data == b'abcd'
        finally:
            try:
                drv.close()
            finally:
                os.close(master)
                os.close(read_fd)


class _ShutdownDone(IoPipelineMessages.AfterFinalInput):
    pass


class _CloseWhenShutdownCompletes(IoPipelineHandler):
    """Application policy: once the output half-close has completed, finish the pipeline."""

    def __init__(self) -> None:
        super().__init__()

        self.final_output = IoPipelineMessages.FinalOutput()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Emit):
            for m in msg.msgs:
                if isinstance(m, IoPipelineMessages.ShutdownOutput):
                    pr = weakref.ref(ctx.pipeline)

                    def on_done(so: ta.Any) -> None:
                        if so.is_succeeded() and (p := pr()) is not None:
                            p.feed_in(_ShutdownDone())

                    m.add_listener(on_done)
                ctx.feed_out(m)
            return

        if isinstance(msg, _ShutdownDone):
            ctx.feed_out(self.final_output)
            return

        ctx.feed_in(msg)


class TestSyncReadFalseLeavesListenerOutput(unittest.TestCase):
    # `next(read=False)` "processes queued and immediately due work". Output produced by a fence-completion listener
    # during its write loop is left sitting in pipeline.output: the driver stays RUNNING with a FinalOutput nobody will
    # process until some later next() call. (fdio's on_writable re-polls after flushing; sync does not.)

    def test_final_output_from_shutdown_listener_is_processed(self) -> None:
        h = _CloseWhenShutdownCompletes()
        so = IoPipelineMessages.ShutdownOutput()
        a, b = socket.socketpair()
        try:
            drv = SocketSyncIoPipelineDriver(_spec(h), a)
            try:
                assert drv.next(read=False) is None
                drv.enqueue(_Emit(b'payload', so))
                assert drv.next(read=False) is None
                assert so.is_succeeded()

                assert drv.pipeline.output.peek() is None, drv.pipeline.output.peek()
                assert h.final_output.is_succeeded()
            finally:
                drv.close()
        finally:
            a.close()
            b.close()


class _SendAllThenFinish(IoPipelineHandler):
    """Sends a payload larger than the socket buffers and finishes at once, reading (and keeping) whatever arrives."""

    def __init__(self, payload: bytes) -> None:
        super().__init__()

        self._payload = payload
        self.final_output = IoPipelineMessages.FinalOutput()
        self.received = 0

        # Outcomes are only observable from listeners (DESIGN 5).
        self.final_exc: ta.Optional[BaseException] = None
        self.final_output.add_listener(self._on_final_done)

    def _on_final_done(self, msg: IoPipelineMessages.Completable) -> None:
        if msg.is_failed():
            self.final_exc = msg.get_exception()

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


class TestDrainingDuplexDeadlock(unittest.TestCase):
    # DESIGN 6: "Output backpressure must never stop input ... two peers each blocked on output, each waiting for the
    # other to read, would otherwise deadlock symmetrically." Both peers send more than the transport holds and then
    # FinalOutput, ignoring each other's input. A draining driver keeps taking input off the transport (and discards
    # it), so one side completes; the other's remaining output then has no reader, which with real sockets fails it.
    # Either way, neither hangs.

    def test_fdio_both_draining(self) -> None:
        payload = b'x' * (4 * 1024 * 1024)
        ha, hb = _SendAllThenFinish(payload), _SendAllThenFinish(payload)
        sa, sb = socket.socketpair()
        poller = SelectFdioPoller()
        da = IoPipelineDriverSocketFdioHandler(sa, ('a', 0), IoPipeline.Spec([ha]))
        db = IoPipelineDriverSocketFdioHandler(sb, ('b', 0), IoPipeline.Spec([hb]))
        mgr = FdioManager(poller)
        try:
            for d in (da, db):
                assert d.next(read=False) is None
                mgr.register(d)

            deadline = time.monotonic() + 5.
            while (da.is_active or db.is_active) and time.monotonic() < deadline:
                try:
                    mgr.poll(timeout=.2)
                except BrokenPipeError:
                    pass

            assert not (da.is_active or db.is_active), (da.state, db.state)
            assert ha.final_output.is_succeeded() or hb.final_output.is_succeeded()
            for d, h in ((da, ha), (db, hb)):
                if not h.final_output.is_succeeded():
                    assert d.state is IoPipelineDriverState.FAILED, d.state
        finally:
            da.close()
            db.close()
            poller.close()

    def test_pure_both_draining_over_bounded_link(self) -> None:
        link_capacity = 256 * 1024
        payload = b'x' * (4 * 1024 * 1024)
        ha, hb = _SendAllThenFinish(payload), _SendAllThenFinish(payload)
        da = PureIoPipelineDriver(IoPipeline.Spec([ha]))
        db = PureIoPipelineDriver(IoPipeline.Spec([hb]))

        def transfer(src: PureIoPipelineDriver, dst: PureIoPipelineDriver) -> bool:
            if not src.is_running:
                return False
            if not dst.is_running:
                if not src.has_pending_output:
                    return False
                # The peer is gone: the next write fails, as a socket's would.
                src.fail_output(BrokenPipeError('peer closed'))
                try:
                    src.drain_output()
                except BrokenPipeError:
                    pass
                else:
                    raise AssertionError('the write to a departed peer did not fail')
                return True
            room = link_capacity - dst.pending_input_bytes
            if room > 0 and src.has_pending_output:
                data = src.drain_output(room)
                if data:
                    dst.feed_input(data)
                    return True
            return False

        try:
            for d in (da, db):
                assert d.next(read=False) is None

            for _ in range(10_000):
                for d in (da, db):
                    if d.is_running:
                        assert d.next(read=True, raise_on_stall=False) is None
                if not (transfer(da, db) | transfer(db, da)):
                    break

            # One side drained everything - its peer kept reading while draining - and closed; the other's remaining
            # output then had no reader, which failed it.
            assert {da.state, db.state} == {IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED}
            for d, h in ((da, ha), (db, hb)):
                if d.state is IoPipelineDriverState.CLOSED:
                    assert h.final_output.is_succeeded()
                else:
                    assert isinstance(h.final_exc, BrokenPipeError), h.final_exc
        finally:
            da.close()
            db.close()
