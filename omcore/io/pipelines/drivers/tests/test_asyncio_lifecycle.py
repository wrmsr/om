# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import typing as ta
import weakref

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...asyncs import AsyncIoPipelineMessages
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...multiplex.handlers import MultiplexIoPipelineHandler
from ...multiplex.tests.apps import app_spec
from ...multiplex.tests.loopback import LoopbackAdapter
from ...multiplex.tests.loopback import LOpen
from ...multiplex.tests.loopback import LReset
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..pure import PureIoPipelineDriver
from ..sync import FdSyncIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver


##


class _Payload:
    pass


class _AwaitApp(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.started = asyncio.Event()
        self.blocker = asyncio.Event()
        self.task = None
        self.await_message = None

    async def run(self):
        self.task = asyncio.current_task()
        self.started.set()
        await self.blocker.wait()

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self.await_message = AsyncIoPipelineMessages.Await(self.run())
            ctx.feed_out(self.await_message)
        if not isinstance(msg, IoPipelineMessages.Error):
            ctx.feed_in(msg)


class TestAsyncioLifecycle(AsyncioIsolatedAsyncTestCase):
    async def test_close_releases_unprocessed_input(self):
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

    async def _driver(self, *handlers):
        sock, peer = socket.socketpair()
        self.addCleanup(peer.close)
        self.addCleanup(sock.close)
        reader, writer = await asyncio.open_connection(sock=sock)
        return PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(handlers, services=[StubIoPipelineFlowService(auto_read=False)]),
            reader,
            writer,
        )

    async def test_close_finishes_unprocessed_enqueue_waitable(self):
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

    async def test_cancelled_enqueue_waiter_does_not_fail_driver(self):
        driver = await self._driver()
        try:
            pending = driver.enqueue_waitable()
            pending.cancel()
            self.assertIsNone(await driver.next(read=False))
            self.assertTrue(driver.pipeline.is_ready)
        finally:
            await driver.close()

    async def test_close_cancels_a_coroutine_started_by_await(self):
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

    async def test_reset_cancels_a_coroutine_started_by_child_await(self):
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
