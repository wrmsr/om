# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import threading
import time
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..sync import FdSyncIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver
from ..sync import SyncIoPipelineDriver
from ..types import IoPipelineDriverState


##


class _SendAndFinish(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.final: ta.Union[IoPipelineMessages.FinalOutput, IoPipelineMessages.ShutdownOutput] = (
            IoPipelineMessages.FinalOutput()
        )

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(b'x' * (1024 * 1024))
            ctx.feed_out(self.final)
        else:
            ctx.feed_in(msg)


def _spec(app):
    # The application needs no more input. Draining its final output must still free transport space for the peer.
    return IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=False)])


def _sockets():
    pair = socket.socketpair()
    for sock in pair:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
    return pair


def _peer(sock, errors):
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


class TestSyncFinalDrain(unittest.TestCase):
    def _run(self, *, fd):
        socks = _sockets()
        app = _SendAndFinish()
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

    def test_socket_final_drain_keeps_receiving(self):
        self._run(fd=False)

    def test_fd_final_drain_keeps_receiving(self):
        self._run(fd=True)


class TestAsyncioFinalDrain(AsyncioIsolatedAsyncTestCase):
    async def test_shutdown_completion_waits_for_transport_half_close(self):
        socks = _sockets()
        app = _SendAndFinish()
        app.final = IoPipelineMessages.ShutdownOutput()
        done = asyncio.Event()
        app.final.add_listener(lambda msg: done.set())
        reader, writer = await asyncio.open_connection(sock=socks[0])
        driver = PollAsyncioStreamIoPipelineDriver(
            _spec(app),
            reader,
            writer,
            config=PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=2 * 1024 * 1024,
                write_low_watermark=1024 * 1024,
            ),
        )
        task = asyncio.create_task(driver.loop_until_done())
        try:
            await asyncio.wait_for(done.wait(), 2.)
            self.assertTrue(app.final.is_succeeded())
            # asyncio's write_eof defers socket.shutdown until its transport buffer is empty.
            self.assertEqual(writer.transport.get_write_buffer_size(), 0)
        finally:
            await driver.close()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            for sock in socks:
                sock.close()

    async def test_final_drain_keeps_receiving(self):
        socks = _sockets()
        app = _SendAndFinish()
        reader, writer = await asyncio.open_connection(sock=socks[0], limit=4096)
        driver = PollAsyncioStreamIoPipelineDriver(_spec(app), reader, writer)
        socks[1].setblocking(False)

        async def peer():
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


class TestFdioFinalDrain(unittest.TestCase):
    def test_final_drain_keeps_receiving(self):
        socks = _sockets()
        app = _SendAndFinish()
        poller = SelectFdioPoller()
        manager = FdioManager(poller)
        driver = IoPipelineDriverSocketFdioHandler(socks[0], ('local', 0), _spec(app))
        socks[1].settimeout(5.)
        errors: ta.List[BaseException] = []
        thread = threading.Thread(target=_peer, args=(socks[1], errors), daemon=True)
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
