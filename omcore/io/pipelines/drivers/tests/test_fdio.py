# ruff: noqa: SLF001
# @om-lite
import socket
import typing as ta
import unittest

from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
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
    def test_invalid_watermarks(self):
        with self.assertRaises(ValueError):
            IoPipelineDriverSocketFdioHandler.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

    def test_read_false_does_not_raise_on_stall(self):
        sock, peer = socket.socketpair()
        with peer:
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
                self.assertIsNone(drv.next(read=False))
            finally:
                drv.close()

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
        assert [bytes(b) for b in drv._write_q] == [b'cd']

        drv._do_write_or_q([b'ef'])
        assert sock.sent == [b'ab']
        assert [bytes(b) for b in drv._write_q] == [b'cd', b'ef']

        drv._try_flush_write_q()
        assert sock.sent == [b'ab', b'cd', b'ef']
        assert not drv._write_q
        assert drv._write_q_bytes == 0

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
            self.assertEqual([bytes(b) for b in drv._write_q], [b'payload'])
            self.assertFalse(sock.closed)
            self.assertTrue(drv.pipeline.is_ready)

            drv.on_writable()

            self.assertEqual(sock.sent, [b'payload'])
            self.assertTrue(sock.closed)
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            drv.close()

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
