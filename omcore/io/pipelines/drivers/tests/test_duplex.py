# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Full-duplex integration: two peers in manual-read mode each send a payload much larger than both the write watermark
and the kernel socket buffers, fence it with FlushOutput and ShutdownOutput, and read until the other side's EOF before
closing with FinalOutput. Neither side may stop reading merely because its own output is blocked - otherwise both
block on output while each waits for the other to read.
"""
import asyncio
import hashlib
import socket
import threading
import time
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..pure import PureIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver
from ..types import IoPipelineDriverState


##


_PAYLOAD_SIZE = 4 * 1024 * 1024
_CHUNK_SIZE = 64 * 1024
_TIMEOUT_S = 30.


def _make_payload(seed: bytes, size: int = _PAYLOAD_SIZE) -> bytes:
    out = bytearray()
    block = hashlib.sha256(seed).digest()
    while len(out) < size:
        out.extend(block)
        block = hashlib.sha256(block).digest()
    return bytes(out[:size])


class _DuplexPeerHandler(IoPipelineHandler):
    def __init__(self, payload: bytes) -> None:
        super().__init__()

        self._payload = payload

        self.received = bytearray()
        self.flush_output = IoPipelineFlowMessages.FlushOutput()
        self.shutdown_output = IoPipelineMessages.ShutdownOutput()
        self.final_output = IoPipelineMessages.FinalOutput()
        self.saw_final_input = False
        self.read_requests = 0

    def _request_input(self, ctx: IoPipelineHandlerContext) -> None:
        self.read_requests += 1
        ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)

            mv = memoryview(self._payload)
            for pos in range(0, len(mv), _CHUNK_SIZE):
                ctx.feed_out(mv[pos:pos + _CHUNK_SIZE])
            ctx.feed_out(self.flush_output)
            ctx.feed_out(self.shutdown_output)

            self._request_input(ctx)
            return

        if ByteStreamBuffers.can_bytes(msg):
            for seg in ByteStreamBuffers.iter_segments(msg):
                self.received.extend(seg)
            return

        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            if not self.saw_final_input:
                self._request_input(ctx)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            ctx.feed_out(self.final_output)
            return

        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            return

        ctx.feed_in(msg)


def _spec(handler: _DuplexPeerHandler) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [handler],
        services=[StubIoPipelineFlowService(auto_read=False)],
    )


class _DuplexCase:
    def __init__(self) -> None:
        super().__init__()

        self.payload_a = _make_payload(b'a')
        self.payload_b = _make_payload(b'b')
        self.handler_a = _DuplexPeerHandler(self.payload_a)
        self.handler_b = _DuplexPeerHandler(self.payload_b)

    def check(self, tc: unittest.TestCase) -> None:
        tc.assertEqual(len(self.handler_a.received), len(self.payload_b))
        tc.assertTrue(bytes(self.handler_a.received) == self.payload_b)
        tc.assertEqual(len(self.handler_b.received), len(self.payload_a))
        tc.assertTrue(bytes(self.handler_b.received) == self.payload_a)

        for h in (self.handler_a, self.handler_b):
            tc.assertTrue(h.flush_output.is_succeeded())
            tc.assertTrue(h.shutdown_output.is_succeeded())
            tc.assertTrue(h.final_output.is_succeeded())
            tc.assertTrue(h.saw_final_input)
            tc.assertGreater(h.read_requests, 1)


##


class TestDuplexAsyncio(AsyncioIsolatedAsyncTestCase):
    async def test_full_duplex_over_socket_pair(self) -> None:
        case = _DuplexCase()
        sock_a, sock_b = socket.socketpair()
        try:
            reader_a, writer_a = await asyncio.open_connection(sock=sock_a)
            reader_b, writer_b = await asyncio.open_connection(sock=sock_b)

            drv_a = PollAsyncioStreamIoPipelineDriver(_spec(case.handler_a), reader_a, writer_a)
            drv_b = PollAsyncioStreamIoPipelineDriver(_spec(case.handler_b), reader_b, writer_b)
            try:
                await asyncio.wait_for(
                    asyncio.gather(drv_a.loop_until_done(), drv_b.loop_until_done()),
                    _TIMEOUT_S,
                )
            finally:
                await drv_a.close()
                await drv_b.close()

            self.assertIs(drv_a.state, IoPipelineDriverState.CLOSED)
            self.assertIs(drv_b.state, IoPipelineDriverState.CLOSED)
            case.check(self)

        finally:
            sock_a.close()
            sock_b.close()

    async def test_full_duplex_over_tcp(self) -> None:
        case = _DuplexCase()
        server_done: asyncio.Future = asyncio.get_running_loop().create_future()

        async def on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            drv = PollAsyncioStreamIoPipelineDriver(_spec(case.handler_b), reader, writer)
            try:
                await drv.loop_until_done()
            except BaseException as e:  # noqa
                server_done.set_exception(e)
            else:
                server_done.set_result(drv.state)
            finally:
                await drv.close()

        server = await asyncio.start_server(on_connect, '127.0.0.1', 0)
        try:
            port = server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection('127.0.0.1', port)
            drv_a = PollAsyncioStreamIoPipelineDriver(_spec(case.handler_a), reader, writer)
            try:
                await asyncio.wait_for(asyncio.gather(drv_a.loop_until_done(), server_done), _TIMEOUT_S)
            finally:
                await drv_a.close()

            self.assertIs(drv_a.state, IoPipelineDriverState.CLOSED)
            self.assertIs(server_done.result(), IoPipelineDriverState.CLOSED)
            case.check(self)

        finally:
            server.close()
            await server.wait_closed()


class TestDuplexFdio(unittest.TestCase):
    def test_full_duplex_in_one_manager(self) -> None:
        case = _DuplexCase()
        sock_a, sock_b = socket.socketpair()
        poller = SelectFdioPoller()
        drv_a = IoPipelineDriverSocketFdioHandler(sock_a, ('a', 0), _spec(case.handler_a))
        drv_b = IoPipelineDriverSocketFdioHandler(sock_b, ('b', 0), _spec(case.handler_b))
        manager = FdioManager(poller)
        try:
            for drv in (drv_a, drv_b):
                self.assertIsNone(drv.next(read=False))
                manager.register(drv)

            deadline = time.monotonic() + _TIMEOUT_S
            while drv_a.is_active or drv_b.is_active:
                self.assertLess(time.monotonic(), deadline, 'full duplex transfer stalled')
                manager.poll(timeout=1.)

            self.assertIs(drv_a.state, IoPipelineDriverState.CLOSED)
            self.assertIs(drv_b.state, IoPipelineDriverState.CLOSED)
            case.check(self)

        finally:
            drv_a.close()
            drv_b.close()
            poller.close()


class TestDuplexSync(unittest.TestCase):
    def test_full_duplex_in_two_threads(self) -> None:
        case = _DuplexCase()
        sock_a, sock_b = socket.socketpair()
        errors: ta.List[BaseException] = []

        # The original socket timeout bounds each readiness wait, so a stall raises rather than hanging the test.
        for sock in (sock_a, sock_b):
            sock.settimeout(_TIMEOUT_S)

        drivers = [
            SocketSyncIoPipelineDriver(_spec(case.handler_a), sock_a),
            SocketSyncIoPipelineDriver(_spec(case.handler_b), sock_b),
        ]

        def run(drv: SocketSyncIoPipelineDriver) -> None:
            try:
                drv.loop_until_done()
            except BaseException as e:  # noqa
                errors.append(e)

        threads = [threading.Thread(target=run, args=(drv,)) for drv in drivers]
        try:
            for t in threads:
                t.start()
            for t in threads:
                t.join(_TIMEOUT_S * 2)
                self.assertFalse(t.is_alive())

            self.assertEqual(errors, [])
            for drv in drivers:
                self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            case.check(self)

        finally:
            sock_a.close()
            sock_b.close()


class TestDuplexPure(unittest.TestCase):
    def test_full_duplex_over_bounded_link(self) -> None:
        # Each direction of the simulated link holds at most this many undelivered bytes, like a socket buffer, so a
        # side which stopped reading while its output was pending would wedge the transfer.
        link_capacity = 256 * 1024

        case = _DuplexCase()
        drv_a = PureIoPipelineDriver(_spec(case.handler_a))
        drv_b = PureIoPipelineDriver(_spec(case.handler_b))
        eof_sent: ta.Set[int] = set()

        def transfer(src: PureIoPipelineDriver, dst: PureIoPipelineDriver) -> bool:
            progressed = False
            if src.is_running and dst.is_running:
                room = link_capacity - dst.pending_input_bytes
                if room > 0 and src.has_pending_output:
                    data = src.drain_output(room)
                    if data:
                        dst.feed_input(data)
                        progressed = True
            if src.output_shutdown and id(src) not in eof_sent and dst.is_running:
                eof_sent.add(id(src))
                dst.feed_eof()
                progressed = True
            return progressed

        try:
            for drv in (drv_a, drv_b):
                self.assertIsNone(drv.next(read=False))

            for _ in range(100_000):
                if not (drv_a.is_running or drv_b.is_running):
                    break

                progressed = False
                for drv in (drv_a, drv_b):
                    if drv.is_running:
                        self.assertIsNone(drv.next(read=True, raise_on_stall=False))
                progressed |= transfer(drv_a, drv_b)
                progressed |= transfer(drv_b, drv_a)

                # Drain whatever remains once the receiving side has gone (final output after both EOFs).
                for drv in (drv_a, drv_b):
                    if drv.state is IoPipelineDriverState.DRAINING and not drv.pending_output_bytes:
                        drv.drain_output()
                        progressed = True

                self.assertTrue(progressed, 'full duplex transfer stalled')

            self.assertIs(drv_a.state, IoPipelineDriverState.CLOSED)
            self.assertIs(drv_b.state, IoPipelineDriverState.CLOSED)
            case.check(self)

        finally:
            drv_a.close()
            drv_b.close()
