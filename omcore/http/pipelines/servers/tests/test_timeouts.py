# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
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
from ....versions import HttpVersions
from ...requests import FullIoPipelineHttpRequest
from ...requests import IoPipelineHttpRequestAborted
from ...requests import IoPipelineHttpRequestBodyData
from ...requests import IoPipelineHttpRequestEnd
from ...requests import IoPipelineHttpRequestHead
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseAborted
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..apps.asgi import AsgiIoPipelineHandler
from ..timeouts import IoPipelineHttpServerRequestTimeoutHandler


def make_request(target: str = '/') -> FullIoPipelineHttpRequest:
    return FullIoPipelineHttpRequest(
        head=IoPipelineHttpRequestHead(
            method='GET',
            target=target,
            headers=HttpHeaders([('Host', 'test')]),
            version=HttpVersions.HTTP_1_1,
        ),
        body=b'',
    )


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


_INFORMATIONAL_RESPONSE = object()
_PARTIAL_RESPONSE = object()
_RESPONSE_END = object()
_RESPONSE_ABORTED = object()


class ResponseControlIoPipelineHandler(CaptureRequestTimeoutIoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _INFORMATIONAL_RESPONSE:
            ctx.feed_out(make_response_head(100))
            ctx.feed_out(IoPipelineHttpResponseEnd())

        elif msg is _PARTIAL_RESPONSE:
            ctx.feed_out(make_response_head())
            ctx.feed_out(IoPipelineHttpResponseBodyData(b'body'))

        elif msg is _RESPONSE_END:
            ctx.feed_out(IoPipelineHttpResponseEnd())

        elif msg is _RESPONSE_ABORTED:
            ctx.feed_out(IoPipelineHttpResponseAborted('aborted'))

        else:
            super().inbound(ctx, msg)


class TimeoutResponseIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.errors: ta.List[IoPipelineMessages.Error] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            ctx.feed_out(FullIoPipelineHttpResponse.simple(status=504, body=b'timed out'))

        elif isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


def make_spec(
        timeout: IoPipelineHttpServerRequestTimeoutHandler,
        handler: IoPipelineHandler,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [timeout, handler],
        services=[StubIoPipelineFlowService(auto_read=False)],
    )


class TestIoPipelineHttpServerRequestTimeoutHandler(unittest.TestCase):
    def test_invalid_timeout(self) -> None:
        for timeout_s in [0., -1., float('inf'), float('-inf'), float('nan')]:
            with self.subTest(timeout_s=timeout_s):
                with self.assertRaises(ValueError):
                    IoPipelineHttpServerRequestTimeoutHandler(timeout_s)

    def test_unconfigured_is_tickless_and_does_not_require_scheduler(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler()
        pipeline = IoPipeline.new(
            [timeout],
            IoPipeline.Config(inbound_terminal='drop'),
        )
        try:
            pipeline.feed_initial_input()
            pipeline.feed_in(make_request())

            self.assertIsNone(timeout._handle)
            self.assertIsNone(pipeline.services.find(IoPipelineScheduling))
        finally:
            pipeline.destroy()

    def test_configured_timeout_requires_scheduler(self) -> None:
        with self.assertRaises(ValueError):
            IoPipeline.new([IoPipelineHttpServerRequestTimeoutHandler(1.)])


class TestSyncIoPipelineHttpServerRequestTimeoutHandler(unittest.TestCase):
    def test_expires_once(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler(.01)
        capture = CaptureRequestTimeoutIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, capture), object())
        try:
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)

            drv.enqueue(make_request('/timeout'))
            error = drv.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(capture.errors), 1)
            self.assertIs(capture.errors[0].exc, error)
            self.assertEqual(capture.errors[0].direction, 'inbound')
            handler_ref = capture.errors[0].handler
            if handler_ref is None:
                self.fail('Expected request timeout handler ref')
            self.assertIs(handler_ref.handler, timeout)

            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
            self.assertIsNone(drv.next(read=False))
            self.assertEqual(len(capture.errors), 1)
        finally:
            drv.close()

    def test_deadline_is_absolute_until_final_response(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler(60.)
        control = ResponseControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))

            head = make_request('/stream').head
            drv.enqueue(head)
            self.assertIsNone(drv.next(read=False))
            handle = timeout._handle
            self.assertIsNotNone(handle)

            drv.enqueue(IoPipelineHttpRequestBodyData(b'body'), IoPipelineHttpRequestEnd())
            self.assertIsNone(drv.next(read=False))
            self.assertIs(timeout._handle, handle)

            drv.enqueue(_INFORMATIONAL_RESPONSE)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseHead)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseEnd)
            self.assertIs(timeout._handle, handle)

            drv.enqueue(_PARTIAL_RESPONSE)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseHead)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseBodyData)
            self.assertIs(timeout._handle, handle)

            drv.enqueue(_RESPONSE_END)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseEnd)
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()

    def test_aborts_and_final_input_cancel(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler(60.)
        control = ResponseControlIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, control), object())
        try:
            self.assertIsNone(drv.next(read=False))

            drv.enqueue(make_request('/request-aborted'))
            self.assertIsNone(drv.next(read=False))
            self.assertIsNotNone(timeout._handle)
            drv.enqueue(IoPipelineHttpRequestAborted('aborted'))
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)

            drv.enqueue(make_request('/response-aborted'))
            self.assertIsNone(drv.next(read=False))
            self.assertIsNotNone(timeout._handle)
            drv.enqueue(_RESPONSE_ABORTED)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseAborted)
            self.assertIsNone(timeout._handle)

            drv.enqueue(make_request('/eof'))
            self.assertIsNone(drv.next(read=False))
            self.assertIsNotNone(timeout._handle)
            drv.enqueue(IoPipelineMessages.FinalInput())
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()

    def test_rejects_overlapping_requests(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler(60.)
        capture = CaptureRequestTimeoutIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, capture), object())
        try:
            self.assertIsNone(drv.next(read=False))

            drv.enqueue(make_request('/first'))
            self.assertIsNone(drv.next(read=False))

            drv.enqueue(make_request('/second'))
            error = drv.next(read=False)
            self.assertIsInstance(error, RuntimeError)
            self.assertIn('pipelining', str(error))
        finally:
            drv.close()

    def test_error_handler_can_complete_exchange(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler(.01)
        response = TimeoutResponseIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, response), object())
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(make_request('/timeout-response'))

            msg = drv.next()
            self.assertIsInstance(msg, FullIoPipelineHttpResponse)
            self.assertEqual(ta.cast(FullIoPipelineHttpResponse, msg).head.status, 504)
            self.assertEqual(len(response.errors), 1)
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()


class TestAsyncioIoPipelineHttpServerRequestTimeoutHandler(AsyncioIsolatedAsyncTestCase):
    async def test_expires(self) -> None:
        timeout = IoPipelineHttpServerRequestTimeoutHandler(.01)
        capture = CaptureRequestTimeoutIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            make_spec(timeout, capture),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue(make_request('/timeout'))

            error = await drv.next()
            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(capture.errors), 1)
            self.assertIs(capture.errors[0].exc, error)
            self.assertIsNone(timeout._handle)
            self.assertEqual(drv._sched._live, set())
        finally:
            await drv.close()

    async def test_timeout_response_closes_suspended_asgi_request(self) -> None:
        pending = asyncio.get_running_loop().create_future()

        async def app(scope, receive, send):
            await pending
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            await send({
                'type': 'http.response.body',
                'body': b'late',
            })

        timeout = IoPipelineHttpServerRequestTimeoutHandler(.01)
        asgi = AsgiIoPipelineHandler(app)
        response = TimeoutResponseIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [timeout, asgi, response],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue(make_request('/asgi-timeout'))

            msg = await drv.next()
            self.assertIsInstance(msg, FullIoPipelineHttpResponse)
            self.assertEqual(ta.cast(FullIoPipelineHttpResponse, msg).head.status, 504)
            self.assertIsNone(asgi._drv)

            pending.set_result(None)
            await asyncio.sleep(0)
            self.assertIsNone(await drv.next(read=False))
            self.assertIsNone(await drv.next(read=False))
        finally:
            await drv.close()
