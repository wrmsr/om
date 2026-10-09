# ruff: noqa: UP006 UP007 UP041 UP045 UP037
# @om-lite
"""
Demonstrations of open findings from reviewing the half-close driver work: each test here fails on purpose until its
finding is resolved. See ../../FINDINGS.md for the discussion.
"""
import asyncio
import socket
import threading
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import TimeoutIoPipelineError
from ...sched.timeouts import WriteTimeoutIoPipelineHandler
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver
from ..types import IoPipelineDriverState


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
    # DESIGN 8: "While draining after FinalOutput, the pure and fdio drivers keep taking input off the transport and
    # discard it: nothing consumes it any more, but a peer whose own output waits for this side to read must not wait
    # forever." The sync driver does not: once it holds a FinalOutput it only waits for writability, so two such
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

        def run(name: str, d: SocketSyncIoPipelineDriver) -> None:
            try:
                d.loop_until_done()
            except BaseException as e:  # noqa
                errors[name] = e

        threads = [
            threading.Thread(target=run, args=('a', da), daemon=True),
            threading.Thread(target=run, args=('b', db), daemon=True),
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
    # The asyncio driver cancels its read task on FinalOutput and then waits for the writer to close - which waits for
    # the transport to flush, which waits for the peer to read. The transport itself stops reading once the stream
    # reader's buffer is full, so two such peers deadlock just like the sync ones.

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
    # DESIGN 7: scheduled callbacks run inside the owning pipeline; DESIGN 8: a driver integrates scheduler deadlines.
    # The asyncio driver handles FinalOutput by awaiting the writer's graceful close inside its command loop, so while
    # a peer which has stopped reading keeps that close from completing, no command - and so no timer, including a
    # WriteTimeoutIoPipelineHandler's - runs. The sync and fdio drivers keep running timers while they wait to write.

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
