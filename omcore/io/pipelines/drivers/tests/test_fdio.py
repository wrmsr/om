# ruff: noqa: SLF001 UP045
# @om-lite
import socket
import time
import typing as ta
import unittest

from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...core import IoPipelineUpdate
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..fdio import IoPipelineDriverSocketFdioHandler
from ..types import IoPipelineDriverState


class ScriptedSendSocket:
    def __init__(self, *send_results):
        super().__init__()

        self._send_results = list(send_results)
        self.sent = []
        self.closed = False
        self.blocking = True

    def setblocking(self, blocking):
        self.blocking = blocking

    def send(self, data):
        if self._send_results:
            result = self._send_results.pop(0)
            if isinstance(result, BaseException):
                raise result
        else:
            result = len(data)

        self.sent.append(bytes(data[:result]))
        return result

    def close(self):
        self.closed = True


class FailingRecvSocket(ScriptedSendSocket):
    def __init__(self, exc: BaseException) -> None:
        super().__init__()

        self._exc = exc

    def recv(self, size: int) -> bytes:
        raise self._exc


class LifecycleIoPipelineService(IoPipelineService):
    def __init__(self, removal_exc: ta.Optional[BaseException] = None) -> None:
        super().__init__()

        self.removed = 0
        self._removal_exc = removal_exc

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'removed':
            self.removed += 1
            if self._removal_exc is not None:
                raise self._removal_exc


_ERROR = object()


class OutputErrorIoPipelineHandler(IoPipelineHandler):
    def __init__(self, error: BaseException) -> None:
        super().__init__()

        self._error = error

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _ERROR:
            ctx.feed_out(self._error)
        else:
            ctx.feed_in(msg)


def fill_socket_send_buffer(sock: socket.socket) -> int:
    timeout = sock.gettimeout()
    sock.setblocking(False)
    total = 0
    try:
        while True:
            try:
                total += sock.send(b'x' * 64 * 1024)
            except BlockingIOError:
                return total
    finally:
        sock.settimeout(timeout)


def drain_socket(sock: socket.socket) -> bytes:
    timeout = sock.gettimeout()
    sock.setblocking(False)
    chunks = []
    try:
        while True:
            try:
                chunks.append(sock.recv(64 * 1024))
            except BlockingIOError:
                return b''.join(chunks)
    finally:
        sock.settimeout(timeout)


class CaptureOutputWritabilityIoPipelineHandler(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.events = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.events.append(msg)
        ctx.feed_in(msg)


_CLOSE = object()


class GracefulCloseIoPipelineHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _CLOSE:
            ctx.feed_out(b'payload')
            ctx.feed_final_output()
        else:
            ctx.feed_in(msg)


class CaptureFinalInputIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.saw_final_input = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
        ctx.feed_in(msg)


class TestIoPipelineDriverSocketFdioHandler(unittest.TestCase):
    def test_repeated_close_destroys_pipeline_once(self) -> None:
        sock: ta.Any = ScriptedSendSocket()
        lifecycle = LifecycleIoPipelineService()
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
        )
        self.assertIsNone(drv.next(read=False))

        drv.close()
        drv.close()

        self.assertEqual(lifecycle.removed, 1)
        self.assertTrue(sock.closed)
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)

    def test_pipeline_output_error_is_non_terminal(self) -> None:
        sock: ta.Any = ScriptedSendSocket()
        error = RuntimeError('pipeline')
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                [OutputErrorIoPipelineHandler(error)],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_ERROR)

            self.assertIs(drv.next(read=False), error)
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(drv.pipeline.is_ready)
            self.assertFalse(sock.closed)
        finally:
            drv.close()

    def test_transport_read_failure_fails_driver(self) -> None:
        error = ConnectionResetError('reset')
        sock: ta.Any = FailingRecvSocket(error)
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(),
        )
        self.assertIsNone(drv.next(read=False))

        with self.assertRaises(ConnectionResetError) as raised:
            drv.on_readable()

        self.assertIs(raised.exception, error)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertTrue(sock.closed)

        drv.close()
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)

    def test_pipeline_removal_failure_fails_close(self) -> None:
        error = RuntimeError('remove')
        sock: ta.Any = ScriptedSendSocket()
        lifecycle = LifecycleIoPipelineService(error)
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
        )
        self.assertIsNone(drv.next(read=False))

        with self.assertRaises(RuntimeError) as raised:
            drv.close()

        self.assertIs(raised.exception, error)
        self.assertEqual(lifecycle.removed, 1)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertTrue(sock.closed)

        drv.close()
        self.assertEqual(lifecycle.removed, 1)

    def test_invalid_chunk_sizes(self):
        with self.assertRaises(ValueError):
            IoPipelineDriverSocketFdioHandler.Config(read_chunk_size=0)
        with self.assertRaises(ValueError):
            IoPipelineDriverSocketFdioHandler.Config(write_chunk_max=0)

    def test_invalid_watermarks(self):
        with self.assertRaises(ValueError):
            IoPipelineDriverSocketFdioHandler.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

    def test_read_false_does_not_raise_on_stall(self):
        sock, peer = socket.socketpair()
        with peer:
            self.assertIsNone(sock.gettimeout())
            drv = IoPipelineDriverSocketFdioHandler(
                sock,
                ('127.0.0.1', 0),
                IoPipeline.Spec(
                    services=[
                        StubIoPipelineFlowService(auto_read=False),
                    ],
                ),
            )
            try:
                self.assertEqual(sock.gettimeout(), 0.)
                self.assertIsNone(drv.next(read=False))
            finally:
                drv.close()

    def test_close_before_pipeline_initialization_closes_socket(self):
        sock, peer = socket.socketpair()
        with peer:
            drv = IoPipelineDriverSocketFdioHandler(
                sock,
                ('127.0.0.1', 0),
                IoPipeline.Spec(),
            )

            drv.close()

            self.assertTrue(drv.closed)
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)

    def test_queues_new_output_behind_existing_backlog(self):
        sock: ta.Any = ScriptedSendSocket(
            2,
            BlockingIOError(),
        )
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(),
        )

        drv._do_write_or_q([b'abcd'])
        assert sock.sent == [b'ab']
        assert [bytes(b) for b in ta.cast(ta.Iterable[ta.Any], drv._write_q)] == [b'cd']

        drv._do_write_or_q([b'ef'])
        assert sock.sent == [b'ab']
        assert [bytes(b) for b in ta.cast(ta.Iterable[ta.Any], drv._write_q)] == [b'cd', b'ef']

        drv._try_flush_write_q()
        assert sock.sent == [b'ab', b'cd', b'ef']
        assert not drv._write_q
        assert drv._write_q_bytes == 0

    def test_write_chunk_max_bounds_each_send(self):
        sock: ta.Any = ScriptedSendSocket()
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(),
            config=IoPipelineDriverSocketFdioHandler.Config(write_chunk_max=2),
        )
        try:
            drv._do_write_or_q([b'abcde'])

            self.assertEqual(sock.sent, [b'ab', b'cd', b'e'])
            self.assertEqual(list(drv._write_q), [])
        finally:
            drv.close()

    def test_zero_progress_send_fails_driver(self):
        sock: ta.Any = ScriptedSendSocket(0)
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(),
        )

        with self.assertRaises(BrokenPipeError):
            drv._do_write_or_q([b'x'])

        self.assertTrue(sock.closed)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)

    def test_output_writability_watermark_transitions(self):
        sock: ta.Any = ScriptedSendSocket(BlockingIOError())
        capture = CaptureOutputWritabilityIoPipelineHandler()
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                [capture],
                services=[
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            config=IoPipelineDriverSocketFdioHandler.Config(
                write_high_watermark=4,
                write_low_watermark=2,
            ),
        )
        try:
            self.assertIsNone(drv.next(read=False))

            self.assertEqual(drv._handle_output(b'abcde'), 'handled')
            self.assertEqual(drv._write_q_bytes, 5)
            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )

            drv.on_writable()
            self.assertEqual(drv._write_q_bytes, 0)
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                ],
            )
        finally:
            drv.close()

    def test_flush_output_completes_after_queued_bytes_are_sent(self) -> None:
        sock: ta.Any = ScriptedSendSocket(BlockingIOError())
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
        )
        flush_output = IoPipelineFlowMessages.FlushOutput()
        completions = []
        flush_output.add_listener(lambda msg: completions.append(msg.is_succeeded()))
        try:
            self.assertIsNone(drv.next(read=False))
            self.assertEqual(drv._handle_output(b'payload'), 'handled')
            self.assertEqual(drv._handle_output(flush_output), 'handled')

            self.assertEqual(drv._write_q_bytes, len(b'payload'))
            self.assertIs(drv._write_q[-1], flush_output)
            self.assertFalse(flush_output.is_done())

            drv.on_writable()

            self.assertEqual(sock.sent, [b'payload'])
            self.assertTrue(flush_output.is_succeeded())
            self.assertEqual(completions, [True])
        finally:
            drv.close()

    def test_final_output_drains_queued_bytes(self) -> None:
        sock: ta.Any = ScriptedSendSocket(BlockingIOError())
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_CLOSE)

            self.assertIsNone(drv.next(read=False))

            self.assertIs(drv.state, IoPipelineDriverState.DRAINING)
            self.assertEqual(
                [bytes(b) for b in ta.cast(ta.Iterable[ta.Any], drv._write_q)],
                [b'payload'],
            )
            self.assertFalse(sock.closed)
            self.assertTrue(drv.pipeline.is_ready)

            drv.on_writable()

            self.assertEqual(sock.sent, [b'payload'])
            self.assertTrue(sock.closed)
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            drv.close()

    def test_close_while_draining_discards_queued_bytes(self) -> None:
        sock: ta.Any = ScriptedSendSocket(BlockingIOError())
        lifecycle = LifecycleIoPipelineService()
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
        )
        self.assertIsNone(drv.next(read=False))
        drv.enqueue(_CLOSE)
        self.assertIsNone(drv.next(read=False))

        self.assertIs(drv.state, IoPipelineDriverState.DRAINING)
        self.assertEqual(drv._write_q_bytes, len(b'payload'))

        drv.close()

        self.assertEqual(drv._write_q_bytes, 0)
        self.assertEqual(list(drv._write_q), [])
        self.assertEqual(lifecycle.removed, 1)
        self.assertTrue(sock.closed)
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
        self.assertFalse(drv.pipeline.is_ready)

    def test_saturated_socket_drains_final_output_when_writable(self) -> None:
        sock, peer = socket.socketpair()
        poller = SelectFdioPoller()
        with peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            drv = IoPipelineDriverSocketFdioHandler(
                sock,
                ('127.0.0.1', 0),
                IoPipeline.Spec(
                    [GracefulCloseIoPipelineHandler()],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
            )
            manager = FdioManager(poller)
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_CLOSE)

                start = time.monotonic()
                self.assertIsNone(drv.next(read=False))
                self.assertLess(time.monotonic() - start, .5)
                self.assertIs(drv.state, IoPipelineDriverState.DRAINING)
                self.assertEqual(drv._write_q_bytes, len(b'payload'))

                manager.register(drv)
                manager.poll(timeout=0.)
                self.assertIs(drv.state, IoPipelineDriverState.DRAINING)

                self.assertTrue(drain_socket(peer))
                manager.poll(timeout=.5)

                self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
                self.assertTrue(drv.closed)
                self.assertEqual(peer.recv(len(b'payload')), b'payload')
            finally:
                drv.close()
                poller.close()

    def test_final_input_does_not_close_output(self) -> None:
        sock: ta.Any = ScriptedSendSocket()
        capture = CaptureFinalInputIoPipelineHandler()
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                [capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(IoPipelineMessages.FinalInput())

            self.assertIsNone(drv.next(read=False))

            self.assertTrue(capture.saw_final_input)
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertFalse(sock.closed)
            self.assertFalse(drv.pipeline.saw_final_output)
        finally:
            drv.close()

    def test_transport_eof_clears_automatic_read_interest(self) -> None:
        sock, peer = socket.socketpair()
        with peer:
            capture = CaptureFinalInputIoPipelineHandler()
            drv = IoPipelineDriverSocketFdioHandler(
                sock,
                ('127.0.0.1', 0),
                IoPipeline.Spec([capture]),
            )
            try:
                self.assertIsNone(drv.next(read=False))
                self.assertTrue(drv.readable())
                peer.shutdown(socket.SHUT_WR)

                drv.on_readable()

                self.assertTrue(capture.saw_final_input)
                self.assertTrue(drv.pipeline.saw_final_input)
                self.assertFalse(drv.readable())
                self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
                self.assertFalse(drv.closed)
            finally:
                drv.close()

    def test_close_discards_queued_bytes(self) -> None:
        sock: ta.Any = ScriptedSendSocket(BlockingIOError())
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
        )
        self.assertIsNone(drv.next(read=False))
        drv._do_write_or_q([b'payload'])
        self.assertEqual(drv._write_q_bytes, 7)

        drv.close()

        self.assertEqual(drv._write_q_bytes, 0)
        self.assertEqual(list(drv._write_q), [])
        self.assertEqual(sock.sent, [])
        self.assertTrue(sock.closed)
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)

    def test_graceful_drain_failure_is_reported(self) -> None:
        error = BrokenPipeError('broken')
        sock: ta.Any = ScriptedSendSocket(BlockingIOError(), error)
        drv = IoPipelineDriverSocketFdioHandler(
            sock,
            ('127.0.0.1', 0),
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_CLOSE)
            self.assertIsNone(drv.next(read=False))
            self.assertIs(drv.state, IoPipelineDriverState.DRAINING)

            with self.assertRaises(BrokenPipeError) as raised:
                drv.on_writable()

            self.assertIs(raised.exception, error)
            self.assertIs(drv.state, IoPipelineDriverState.FAILED)
            self.assertTrue(sock.closed)
            self.assertEqual(list(drv._write_q), [])
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
