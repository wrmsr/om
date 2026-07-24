# ruff: noqa: SLF001 UP006
# @om-lite
import asyncio
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.sync import SyncSocketIoPipelineDriver
from ...errors import IoPipelineError
from ...errors import TimeoutIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..timeouts import ReadTimeoutIoPipelineHandler


class CaptureReadTimeoutIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.errors: ta.List[IoPipelineMessages.Error] = []
        self.reads: ta.List[bytes] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            ctx.feed_out(msg.exc)

        elif isinstance(msg, bytes):
            self.reads.append(msg)

        else:
            ctx.feed_in(msg)


def make_spec(
        timeout: ReadTimeoutIoPipelineHandler,
        capture: CaptureReadTimeoutIoPipelineHandler,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [
            timeout,
            capture,
        ],
        services=[
            StubIoPipelineFlowService(auto_read=False),
        ],
    )


class TestTimeoutIoPipelineError(unittest.TestCase):
    def test_error_hierarchy(self):
        error = TimeoutIoPipelineError()

        self.assertIsInstance(error, IoPipelineError)
        self.assertIsInstance(error, TimeoutError)


class TestSyncReadTimeoutIoPipelineHandler(unittest.TestCase):
    def test_expires(self):
        timeout = ReadTimeoutIoPipelineHandler(.01)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, capture), object())
        try:
            error = drv.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(capture.errors), 1)
            self.assertIs(capture.errors[0].exc, error)
            self.assertEqual(capture.errors[0].direction, 'inbound')
            handler_ref = capture.errors[0].handler
            if handler_ref is None:
                self.fail('Expected timeout handler ref')
            self.assertIs(handler_ref.handler, timeout)

            self.assertIsNone(drv.next(read=False))
            self.assertEqual(len(capture.errors), 1)
        finally:
            drv.close()

    def test_resets_and_stops_at_final_input(self):
        timeout = ReadTimeoutIoPipelineHandler(60.)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, capture), object())
        try:
            self.assertIsNone(drv.next(read=False))
            first_handle = timeout._handle
            self.assertIsNotNone(first_handle)

            drv.enqueue(IoPipelineFlowMessages.FlushInput())
            self.assertIsNone(drv.next(read=False))
            self.assertIs(timeout._handle, first_handle)

            drv.enqueue(b'read')
            self.assertIsNone(drv.next(read=False))
            second_handle = timeout._handle
            self.assertIsNotNone(second_handle)
            self.assertIsNot(second_handle, first_handle)
            self.assertEqual(capture.reads, [b'read'])

            drv.enqueue(IoPipelineMessages.FinalInput())
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()


class TestAsyncioReadTimeoutIoPipelineHandler(AsyncioIsolatedAsyncTestCase):
    async def test_expires(self):
        timeout = ReadTimeoutIoPipelineHandler(.01)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            make_spec(timeout, capture),
            asyncio.StreamReader(),
        )
        try:
            error = await drv.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(capture.errors), 1)
            self.assertIs(capture.errors[0].exc, error)
            self.assertEqual(capture.errors[0].direction, 'inbound')
            handler_ref = capture.errors[0].handler
            if handler_ref is None:
                self.fail('Expected timeout handler ref')
            self.assertIs(handler_ref.handler, timeout)

            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(len(capture.errors), 1)
        finally:
            await drv.close()

    async def test_resets_and_stops_at_final_input(self):
        timeout = ReadTimeoutIoPipelineHandler(60.)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            make_spec(timeout, capture),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            first_handle = timeout._handle
            self.assertIsNotNone(first_handle)

            drv.enqueue(IoPipelineFlowMessages.FlushInput())
            self.assertIsNone(await drv.next(read=False))
            self.assertIs(timeout._handle, first_handle)

            drv.enqueue(b'read')
            self.assertIsNone(await drv.next(read=False))
            second_handle = timeout._handle
            self.assertIsNotNone(second_handle)
            self.assertIsNot(second_handle, first_handle)
            self.assertEqual(capture.reads, [b'read'])

            drv.enqueue(IoPipelineMessages.FinalInput())
            self.assertIsNone(await drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertEqual(drv._sched._live, set())
        finally:
            await drv.close()
