# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...multiplex.handlers import IoPipelineMultiplexConfig
from ...multiplex.tests.apps import StreamApp
from ...multiplex.tests.apps import app_spec
from ...multiplex.tests.h2like import H2LikeAdapter
from ...multiplex.tests.h2like import h2_like_spec
from ...multiplex.types import IoPipelineMultiplexMessages
from ..asyncio import PollAsyncioStreamIoPipelineDriver
from ..sync import SocketSyncIoPipelineDriver
from .producers import DEFER_N_CHUNKS
from .producers import DeferYieldingProducer


def _fill_socket_send_buffer(sock: socket.socket) -> None:
    while True:
        try:
            sock.send(b'x' * (64 * 1024))
        except BlockingIOError:
            return


class TestAsyncioDeferYieldingProducer(AsyncioIsolatedAsyncTestCase):
    async def test_defer_yielding_producer_is_paused_before_exhausting_its_data(self) -> None:
        sock, peer = socket.socketpair()
        sock.setblocking(False)
        peer.setblocking(False)
        _fill_socket_send_buffer(sock)  # the peer never reads, so every further byte backs up in the transport

        try:
            reader, writer = await asyncio.open_connection(sock=sock)
            handler = DeferYieldingProducer()
            driver = PollAsyncioStreamIoPipelineDriver(
                IoPipeline.Spec([handler], services=[StubIoPipelineFlowService(auto_read=False)]),
                reader,
                writer,
                PollAsyncioStreamIoPipelineDriver.Config(
                    write_high_watermark=64 * 1024,
                    write_low_watermark=16 * 1024,
                ),
            )
            try:
                for _ in range(16):
                    self.assertIsNone(await asyncio.wait_for(driver.next(read=False), 5.))
                    await asyncio.sleep(0)

                # Parity with the sync driver (see below): the producer must be paused once the transport holds more
                # than the high watermark - a handful of 16 KiB chunks - not after it has handed over all of its data.
                self.assertIsNotNone(handler.emitted_at_first_pause)
                self.assertLess(check_not_none(handler.emitted_at_first_pause), DEFER_N_CHUNKS)
                self.assertLessEqual(check_not_none(handler.emitted_at_first_pause), 8)

            finally:
                await driver.close()

        finally:
            sock.close()
            peer.close()

    async def test_defer_yielding_producer_does_not_starve_the_event_loop(self) -> None:
        # While a drain is pending, a Defer is run straight from the driver's inner output loop, which never awaits; a
        # producer continuing through Defers therefore runs to exhaustion in one synchronous stretch - no other task on
        # the loop runs, including the drain itself.
        sock, peer = socket.socketpair()
        sock.setblocking(False)
        peer.setblocking(False)
        _fill_socket_send_buffer(sock)

        ticks: ta.List[int] = []
        stop = asyncio.Event()

        async def ticker() -> None:
            while not stop.is_set():
                ticks.append(handler.emitted)
                await asyncio.sleep(0)

        try:
            reader, writer = await asyncio.open_connection(sock=sock)
            handler = DeferYieldingProducer()
            driver = PollAsyncioStreamIoPipelineDriver(
                IoPipeline.Spec([handler], services=[StubIoPipelineFlowService(auto_read=False)]),
                reader,
                writer,
                PollAsyncioStreamIoPipelineDriver.Config(
                    write_high_watermark=64 * 1024,
                    write_low_watermark=16 * 1024,
                ),
            )
            t = asyncio.create_task(ticker())
            await asyncio.sleep(0)
            try:
                self.assertIsNone(await asyncio.wait_for(driver.next(read=False), 5.))
                await asyncio.sleep(0)
                # The other task must have observed the producer at some point other than "nothing" or "everything".
                self.assertTrue(any(0 < n < DEFER_N_CHUNKS for n in ticks), ticks[-5:])
            finally:
                stop.set()
                await t
                await driver.close()

        finally:
            sock.close()
            peer.close()


def check_not_none(v: ta.Optional[int]) -> int:
    assert v is not None
    return v


class TestSyncDeferYieldingProducer(unittest.TestCase):
    def test_sync_driver_pauses_defer_yielding_producer(self) -> None:
        sock, peer = socket.socketpair()
        sock.setblocking(False)
        peer.setblocking(False)
        _fill_socket_send_buffer(sock)

        try:
            handler = DeferYieldingProducer()
            driver = SocketSyncIoPipelineDriver(
                IoPipeline.Spec([handler], services=[StubIoPipelineFlowService(auto_read=False)]),
                sock,
                SocketSyncIoPipelineDriver.Config(
                    write_high_watermark=64 * 1024,
                    write_low_watermark=16 * 1024,
                ),
            )
            try:
                for _ in range(16):
                    driver.next(read=False)
                self.assertIsNotNone(handler.emitted_at_first_pause)
                self.assertLessEqual(check_not_none(handler.emitted_at_first_pause), 8)
            finally:
                driver.close()

        finally:
            sock.close()
            peer.close()


class TestAsyncioMultiplexTurnBudget(AsyncioIsolatedAsyncTestCase):
    async def test_multiplex_turn_budget_bounds_parent_queue(self) -> None:
        # The multiplex handler emits at most turn_output_budget per turn and continues through a parent Defer, relying
        # on the parent driver reporting writability (PauseOutput) before that Defer runs. Once a parent FlushOutput
        # (here: one stream's child flush) has left a drain pending, every continuation Defer runs at once, so all of
        # the other stream's data is moved into the driver's post-drain queue in one go, never paused.
        big = 4 * 1024 * 1024
        budget = 64 * 1024

        sock, peer = socket.socketpair()
        sock.setblocking(False)
        peer.setblocking(False)
        _fill_socket_send_buffer(sock)

        try:
            spec, mux = h2_like_spec(
                'client',
                lambda o: None,  # type: ignore[arg-type,return-value]
                adapter=H2LikeAdapter('client', peer_initial_window=2 * big, max_frame=16 * 1024),
                config=IoPipelineMultiplexConfig(turn_output_budget=budget),
                connection_send_window=2 * big,
            )
            reader, writer = await asyncio.open_connection(sock=sock)
            driver = PollAsyncioStreamIoPipelineDriver(
                spec,
                reader,
                writer,
                PollAsyncioStreamIoPipelineDriver.Config(
                    write_high_watermark=64 * 1024,
                    write_low_watermark=16 * 1024,
                ),
            )
            try:
                self.assertIsNone(await driver.next(read=False))
                small = StreamApp(send=b'a' * 100, send_messages=[IoPipelineFlowMessages.FlushOutput()])
                large = StreamApp(send=b'b' * big, chunk_size=64 * 1024)
                driver.enqueue(
                    IoPipelineMultiplexMessages.OpenStream(app_spec(small), None),
                    IoPipelineMultiplexMessages.OpenStream(app_spec(large), None),
                )
                for _ in range(8):
                    self.assertIsNone(await asyncio.wait_for(driver.next(read=False), 10.))
                    await asyncio.sleep(0)

                held = sum(
                    ByteStreamBuffers.bytes_len(m)
                    for m in driver._post_drain_output_q
                    if ByteStreamBuffers.can_bytes(m)
                )
                queued_in_streams = sum(s.out_bytes for s in mux.streams)
                # Byte accounting should stay honest at the stream layer: nearly all of the large stream's data should
                # still be queued there, not handed to the driver while the transport is far above its high watermark.
                self.assertGreater(queued_in_streams, big // 2, (queued_in_streams, held))
            finally:
                await driver.close()

        finally:
            sock.close()
            peer.close()
