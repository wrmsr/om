# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from .....io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from .....io.pipelines.errors import TimeoutIoPipelineError
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.sched.types import IoPipelineScheduling
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....headers import HttpHeaders
from ...requests import FullIoPipelineHttpRequest
from ...requests import IoPipelineHttpRequestAborted
from ...requests import IoPipelineHttpRequestBodyData
from ...requests import IoPipelineHttpRequestEnd
from ...responses import IoPipelineHttpResponseAborted
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..clients import IoPipelineHttpClientHandler
from ..clients import IoPipelineHttpClientMessages
from ..timeouts import IoPipelineHttpClientRequestTimeoutHandler


def make_request(target: str = '/') -> FullIoPipelineHttpRequest:
    return FullIoPipelineHttpRequest.simple('test', target)


def make_response_head(status: int = 200) -> IoPipelineHttpResponseHead:
    return IoPipelineHttpResponseHead(
        status=status,
        reason=IoPipelineHttpResponseHead.get_reason_phrase(status),
        headers=HttpHeaders([]),
    )


class CaptureRequestTimeoutIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.errors: ta.List[IoPipelineMessages.Error] = []
        self.messages: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            ctx.feed_out(msg.exc)

        elif isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)

        else:
            self.messages.append(msg)


_REQUEST_HEAD = object()
_REQUEST_BODY = object()
_REQUEST_END = object()
_REQUEST_ABORTED = object()
_FINAL_OUTPUT = object()


class RequestControlIoPipelineHandler(CaptureRequestTimeoutIoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _REQUEST_HEAD:
            ctx.feed_out(make_request('/stream').head)

        elif msg is _REQUEST_BODY:
            ctx.feed_out(IoPipelineHttpRequestBodyData(b'body'))

        elif msg is _REQUEST_END:
            ctx.feed_out(IoPipelineHttpRequestEnd())

        elif msg is _REQUEST_ABORTED:
            ctx.feed_out(IoPipelineHttpRequestAborted('aborted'))

        elif msg is _FINAL_OUTPUT:
            ctx.feed_final_output()

        else:
            super().inbound(ctx, msg)


def make_spec(
        timeout: IoPipelineHttpClientRequestTimeoutHandler,
        handler: IoPipelineHandler,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [timeout, handler],
        services=[StubIoPipelineFlowService(auto_read=False)],
    )


class TestIoPipelineHttpClientRequestTimeoutHandler(unittest.TestCase):
    def test_invalid_timeout(self) -> None:
        for timeout_s in [0., -1., float('inf'), float('-inf'), float('nan')]:
            with self.subTest(timeout_s=timeout_s):
                with self.assertRaises(ValueError):
                    IoPipelineHttpClientRequestTimeoutHandler(timeout_s)

    def test_unconfigured_is_tickless_and_does_not_require_scheduler(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler()
        pipeline = IoPipeline.new(
            [timeout],
            IoPipeline.Config(inbound_terminal='drop'),
        )
        try:
            pipeline.feed_initial_input()

            self.assertIsNone(timeout._handle)
            self.assertIsNone(pipeline.services.find(IoPipelineScheduling))
        finally:
            pipeline.destroy()

    def test_configured_timeout_requires_scheduler(self) -> None:
        with self.assertRaises(ValueError):
            IoPipeline.new([IoPipelineHttpClientRequestTimeoutHandler(1.)])


class TestSyncIoPipelineHttpClientRequestTimeoutHandler(unittest.TestCase):
    def test_expires_once(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(.01)
        control = RequestControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)

            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))
            error = drv.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(control.errors), 1)
            self.assertIs(control.errors[0].exc, error)
            self.assertEqual(control.errors[0].direction, 'inbound')
            handler_ref = control.errors[0].handler
            if handler_ref is None:
                self.fail('Expected request timeout handler ref')
            self.assertIs(handler_ref.handler, timeout)

            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
            self.assertIsNone(drv.next(read=False))
            self.assertEqual(len(control.errors), 1)
        finally:
            drv.close()

    def test_deadline_is_absolute_until_final_response(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(60.)
        control = RequestControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))

            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))
            handle = timeout._handle
            self.assertIsNotNone(handle)

            drv.enqueue(_REQUEST_BODY, _REQUEST_END)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpRequestBodyData)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpRequestEnd)
            self.assertIs(timeout._handle, handle)

            drv.enqueue(make_response_head(100), IoPipelineHttpResponseEnd())
            self.assertIsNone(drv.next(read=False))
            self.assertIs(timeout._handle, handle)

            drv.enqueue(make_response_head(), IoPipelineHttpResponseBodyData(b'body'))
            self.assertIsNone(drv.next(read=False))
            self.assertIs(timeout._handle, handle)

            drv.enqueue(IoPipelineHttpResponseEnd())
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()

    def test_aborts_and_final_input_cancel(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(60.)
        control = RequestControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))

            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))
            self.assertIsNotNone(timeout._handle)
            drv.enqueue(_REQUEST_ABORTED)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpRequestAborted)
            self.assertIsNone(timeout._handle)

            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))
            self.assertIsNotNone(timeout._handle)
            drv.enqueue(IoPipelineHttpResponseAborted('aborted'))
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)

            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))
            self.assertIsNotNone(timeout._handle)
            drv.enqueue(IoPipelineMessages.FinalInput())
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()

    def test_final_output_cancels(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(60.)
        control = RequestControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))
            self.assertIsNotNone(timeout._handle)

            drv.enqueue(_FINAL_OUTPUT)
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            drv.close()

    def test_rejects_overlapping_requests(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(60.)
        control = RequestControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))

            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(drv.next(read=False), type(make_request().head))

            drv.enqueue(_REQUEST_HEAD)
            error = drv.next(read=False)
            self.assertIsInstance(error, RuntimeError)
            self.assertIn('Overlapping', str(error))
        finally:
            drv.close()

    def test_client_handler_surfaces_timeout_and_closes(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(.01)
        left, right = socket.socketpair()
        drv = SyncSocketIoPipelineDriver(
            make_spec(timeout, IoPipelineHttpClientHandler()),
            left,
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(IoPipelineHttpClientMessages.Request(make_request('/timeout')))
            self.assertIsInstance(drv.next(read=False), FullIoPipelineHttpRequest)

            error = drv.next()
            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertIsNone(timeout._handle)

            self.assertIsNone(drv.next(read=False))
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            drv.close()
            left.close()
            right.close()


class TestAsyncioIoPipelineHttpClientRequestTimeoutHandler(AsyncioIsolatedAsyncTestCase):
    async def test_expires(self) -> None:
        timeout = IoPipelineHttpClientRequestTimeoutHandler(.01)
        control = RequestControlIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            make_spec(timeout, control),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue(_REQUEST_HEAD)
            self.assertIsInstance(await drv.next(read=False), type(make_request().head))

            error = await drv.next()
            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(control.errors), 1)
            self.assertIs(control.errors[0].exc, error)
            self.assertIsNone(timeout._handle)
            self.assertEqual(drv._sched._live, set())
        finally:
            await drv.close()
