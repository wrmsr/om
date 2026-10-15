# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
"""
Two pipelines on one thread handing work to each other through posting, under each driver: each post runs in its
target's own turn, never nested in the turn which made it, and an idle driver is woken for it.
"""
import asyncio
import socket
import time
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...posting.types import IoPipelinePosting
from ..asyncio.streams import PollAsyncioStreamIoPipelineDriver
from ..fdio.sockets import IoPipelineDriverSocketFdioHandler
from ..pure.drivers import PureIoPipelineDriver
from ..sync.sockets import SocketSyncIoPipelineDriver


##


class _PingPongIoPipelineHandler(IoPipelineHandler):
    """
    Receives a count through a post, records it, and posts the next count into its peer - from inside its own turn.
    `active` is the handler whose turn is in progress, checked on entry to prove posts never nest.
    """

    active: ta.ClassVar[ta.Optional['_PingPongIoPipelineHandler']] = None

    def __init__(
            self,
            name: str,
            limit: int,
            *,
            on_limit: ta.Optional[ta.Callable[[], None]] = None,
    ) -> None:
        super().__init__()

        self.name = name
        self.limit = limit
        self.on_limit = on_limit
        self.received: ta.List[int] = []
        self.nested = 0
        self.peer: ta.Optional[ta.Tuple[IoPipelinePosting, IoPipelineHandlerRef]] = None

    def receive(self, ctx: IoPipelineHandlerContext, n: int) -> None:
        if _PingPongIoPipelineHandler.active is not None:
            self.nested += 1
        _PingPongIoPipelineHandler.active = self
        try:
            self.received.append(n)
            if n < self.limit and self.peer is not None:
                posting, ref = self.peer
                posting.post_context(ref, lambda peer_ctx: peer_ctx.handler.receive(peer_ctx, n + 1))  # type: ignore[attr-defined]  # noqa
            elif n >= self.limit and (on_limit := self.on_limit) is not None:
                on_limit()
        finally:
            _PingPongIoPipelineHandler.active = None


def _wire(a_pipeline: IoPipeline, b_pipeline: IoPipeline) -> ta.Tuple[_PingPongIoPipelineHandler, _PingPongIoPipelineHandler]:  # noqa
    a_ref = a_pipeline.handlers()[0]
    b_ref = b_pipeline.handlers()[0]
    a = ta.cast(_PingPongIoPipelineHandler, a_ref.handler)
    b = ta.cast(_PingPongIoPipelineHandler, b_ref.handler)
    a.peer = (b_pipeline.services[IoPipelinePosting], b_ref)
    b.peer = (a_pipeline.services[IoPipelinePosting], a_ref)
    return a, b


def _unwire(*handlers: _PingPongIoPipelineHandler) -> None:
    for h in handlers:
        h.peer = None


def _kick(a_pipeline: IoPipeline) -> None:
    a_ref = a_pipeline.handlers()[0]
    a_pipeline.services[IoPipelinePosting].post_context(a_ref, lambda ctx: ctx.handler.receive(ctx, 1))  # type: ignore[attr-defined]  # noqa


_LIMIT = 40


class _Checks:
    def check(self: ta.Any, a: _PingPongIoPipelineHandler, b: _PingPongIoPipelineHandler) -> None:
        self.assertEqual(a.received, list(range(1, _LIMIT + 1, 2)))
        self.assertEqual(b.received, list(range(2, _LIMIT + 1, 2)))
        self.assertEqual(a.nested, 0)
        self.assertEqual(b.nested, 0)


class TestPostingPingPongPure(unittest.TestCase, _Checks):
    def test_ping_pong(self) -> None:
        da = PureIoPipelineDriver(IoPipeline.Spec([_PingPongIoPipelineHandler('a', _LIMIT)]))
        db = PureIoPipelineDriver(IoPipeline.Spec([_PingPongIoPipelineHandler('b', _LIMIT)]))
        try:
            self.assertIsNone(da.next(read=False))
            self.assertIsNone(db.next(read=False))
            a, b = _wire(da.pipeline, db.pipeline)
            _kick(da.pipeline)

            for _ in range(_LIMIT + 2):
                self.assertIsNone(da.next(read=False))
                self.assertIsNone(db.next(read=False))

            self.check(a, b)
            _unwire(a, b)
        finally:
            da.close()
            db.close()


class TestPostingPingPongSync(unittest.TestCase, _Checks):
    def test_ping_pong(self) -> None:
        sa, pa = socket.socketpair()
        sb, pb = socket.socketpair()
        da = SocketSyncIoPipelineDriver(IoPipeline.Spec([_PingPongIoPipelineHandler('a', _LIMIT)]), sa)
        db = SocketSyncIoPipelineDriver(IoPipeline.Spec([_PingPongIoPipelineHandler('b', _LIMIT)]), sb)
        try:
            self.assertIsNone(da.next(read=False))
            self.assertIsNone(db.next(read=False))
            a, b = _wire(da.pipeline, db.pipeline)
            _kick(da.pipeline)

            for _ in range(_LIMIT + 2):
                self.assertIsNone(da.next(read=False))
                self.assertIsNone(db.next(read=False))

            self.check(a, b)
            _unwire(a, b)
        finally:
            da.close()
            db.close()
            for s in (sa, pa, sb, pb):
                s.close()


class TestPostingPingPongFdio(unittest.TestCase, _Checks):
    def test_ping_pong_wakes_the_manager(self) -> None:
        sa, pa = socket.socketpair()
        sb, pb = socket.socketpair()
        da = IoPipelineDriverSocketFdioHandler(sa, ('a', 0), IoPipeline.Spec([_PingPongIoPipelineHandler('a', _LIMIT)]))
        db = IoPipelineDriverSocketFdioHandler(sb, ('b', 0), IoPipeline.Spec([_PingPongIoPipelineHandler('b', _LIMIT)]))
        manager = FdioManager(SelectFdioPoller())
        try:
            self.assertIsNone(da.next(read=False))
            self.assertIsNone(db.next(read=False))
            manager.register(da)
            manager.register(db)
            a, b = _wire(da.pipeline, db.pipeline)

            # Idle: neither has anything due.
            self.assertIsNone(da.next_deadline())
            self.assertIsNone(db.next_deadline())

            _kick(da.pipeline)
            self.assertLessEqual(ta.cast(float, da.next_deadline()), time.monotonic())

            # No descriptor ever becomes readable and no timer is set: only the posts wake the manager, promptly.
            started = time.monotonic()
            polls = 0
            while len(b.received) < _LIMIT // 2:
                manager.poll(timeout=5.)
                polls += 1
                self.assertLess(time.monotonic() - started, 4.)

            self.check(a, b)
            self.assertLessEqual(polls, _LIMIT + 1)
            self.assertIsNone(da.next_deadline())
            self.assertIsNone(db.next_deadline())
            _unwire(a, b)
        finally:
            da.close()
            db.close()
            for s in (pa, pb):
                s.close()


class TestPostingPingPongAsyncio(AsyncioIsolatedAsyncTestCase, _Checks):
    async def test_ping_pong_wakes_waiting_drivers(self) -> None:
        done = asyncio.Event()
        da = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec([_PingPongIoPipelineHandler('a', _LIMIT, on_limit=done.set)]),
            asyncio.StreamReader(),
        )
        db = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec([_PingPongIoPipelineHandler('b', _LIMIT, on_limit=done.set)]),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await da.next(read=False))
            self.assertIsNone(await db.next(read=False))
            a, b = _wire(da.pipeline, db.pipeline)

            async def drive(d: PollAsyncioStreamIoPipelineDriver) -> None:
                # Each driver waits on its command queue: only the other's posts wake it.
                while d.is_running:
                    self.assertIsNone(await d.next(raise_on_stall=False))

            ta_ = asyncio.create_task(drive(da))
            tb_ = asyncio.create_task(drive(db))
            try:
                _kick(da.pipeline)

                await asyncio.wait_for(done.wait(), 5.)
                self.check(a, b)
                _unwire(a, b)
            finally:
                await da.close()
                await db.close()
                for t in (ta_, tb_):
                    t.cancel()
                await asyncio.gather(ta_, tb_, return_exceptions=True)
        finally:
            await da.close()
            await db.close()


class _PostingMarker(IoPipelineMessages.AfterShutdownOutput):
    pass


class _NopIoPipelineHandler(IoPipelineHandler):
    pass


class TestPostingWakes(AsyncioIsolatedAsyncTestCase):
    async def test_post_wakes_a_waiting_asyncio_next(self) -> None:
        drv = PollAsyncioStreamIoPipelineDriver(IoPipeline.Spec([_NopIoPipelineHandler()]), asyncio.StreamReader())
        try:
            self.assertIsNone(await drv.next(read=False))
            ref = drv.pipeline.handlers()[0]
            marker = _PostingMarker()

            next_task = asyncio.create_task(drv.next(raise_on_stall=False))
            await asyncio.sleep(0)
            self.assertFalse(next_task.done())

            post = drv.pipeline.services[IoPipelinePosting].post_context(ref, lambda ctx: ctx.feed_out(marker))

            self.assertIs(await asyncio.wait_for(next_task, 1.), marker)
            self.assertTrue(post.is_succeeded())
        finally:
            await drv.close()
