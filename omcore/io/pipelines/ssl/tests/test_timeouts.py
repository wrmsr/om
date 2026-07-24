# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import ssl
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.sync import SyncSocketIoPipelineDriver
from ...errors import TimeoutIoPipelineError
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ..handlers import SslIoPipelineHandler


class ManualSchedulingService(IoPipelineScheduling, IoPipelineService):
    class Handle(IoPipelineScheduling.Handle):
        def __init__(
                self,
                handler_ref: IoPipelineHandlerRef,
                delay_s: float,
                fn: ta.Callable[[], None],
        ) -> None:
            self.handler_ref = handler_ref
            self.delay_s = delay_s
            self.fn = fn

            self.cancelled = False
            self.done = False

        def cancel(self) -> None:
            self.cancelled = True

        def fire(self) -> None:
            if self.cancelled or self.done:
                return

            self.done = True
            with self.handler_ref.pipeline.enter():
                self.fn()

    def __init__(self) -> None:
        super().__init__()

        self.handles: ta.List[ManualSchedulingService.Handle] = []

    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> IoPipelineScheduling.Handle:
        handle = self.Handle(handler_ref, delay_s, fn)
        self.handles.append(handle)
        return handle

    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        for handle in self.handles:
            if handler_ref is None or handle.handler_ref is handler_ref:
                handle.cancel()

    def single_live(self) -> Handle:
        live = [handle for handle in self.handles if not handle.cancelled and not handle.done]
        if len(live) != 1:
            raise AssertionError(live)
        return live[0]


class StallingSslObject:
    def __init__(self, *, handshake_pending: bool) -> None:
        self.handshake_pending = handshake_pending
        self.shutdown_pending = True

    def do_handshake(self) -> None:
        if self.handshake_pending:
            raise ssl.SSLWantReadError

    def pending(self) -> int:
        return 0

    def read(self, size: int) -> bytes:
        raise ssl.SSLWantReadError

    def unwrap(self) -> None:
        if self.shutdown_pending:
            raise ssl.SSLWantReadError


class StallingSslContext:
    def __init__(self, ssl_obj: StallingSslObject) -> None:
        self.ssl_obj = ssl_obj

    def wrap_bio(self, *args: ta.Any, **kwargs: ta.Any) -> StallingSslObject:
        return self.ssl_obj


class Close:
    def __init__(self, final_output: IoPipelineMessages.FinalOutput) -> None:
        self.final_output = final_output


class CaptureTimeoutIoPipelineHandler(IoPipelineHandler):
    def __init__(self, *, output_errors: bool = False) -> None:
        super().__init__()

        self.output_errors = output_errors
        self.errors: ta.List[IoPipelineMessages.Error] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            if self.output_errors:
                ctx.feed_out(msg.exc)

        elif isinstance(msg, Close):
            ctx.feed_out(msg.final_output)

        else:
            ctx.feed_in(msg)


def make_pipeline(
        ssl_obj: StallingSslObject,
        config: SslIoPipelineHandler.Config,
) -> ta.Tuple[
    IoPipeline,
    SslIoPipelineHandler,
    CaptureTimeoutIoPipelineHandler,
    ManualSchedulingService,
]:
    sched = ManualSchedulingService()
    handler = SslIoPipelineHandler(
        ta.cast(ssl.SSLContext, StallingSslContext(ssl_obj)),
        server_side=True,
        config=config,
    )
    capture = CaptureTimeoutIoPipelineHandler()
    pipeline = IoPipeline(IoPipeline.Spec(
        [
            handler,
            capture,
        ],
        services=[sched],
    ))
    return pipeline, handler, capture, sched


class TestSslIoPipelineHandlerTimeouts(unittest.TestCase):
    def test_config_validation(self):
        for value in (0., -1., float('inf'), float('-inf'), float('nan')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    SslIoPipelineHandler.Config(handshake_timeout_s=value)
                with self.assertRaises(ValueError):
                    SslIoPipelineHandler.Config(shutdown_timeout_s=value)

    def test_timeouts_are_disabled_by_default(self):
        ssl_obj = StallingSslObject(handshake_pending=True)
        handler = SslIoPipelineHandler(
            ta.cast(ssl.SSLContext, StallingSslContext(ssl_obj)),
            server_side=True,
        )
        with IoPipeline.new([handler]) as pipeline:
            pipeline.feed_initial_input()
            self.assertEqual(handler.state, SslIoPipelineHandler.State.HANDSHAKE)

    def test_enabled_timeout_requires_scheduler(self):
        ssl_obj = StallingSslObject(handshake_pending=True)
        handler = SslIoPipelineHandler(
            ta.cast(ssl.SSLContext, StallingSslContext(ssl_obj)),
            server_side=True,
            config=SslIoPipelineHandler.Config(handshake_timeout_s=3.),
        )
        with self.assertRaises(ValueError):
            IoPipeline.new([handler])

    def test_handshake_timeout_is_absolute_and_closes(self):
        ssl_obj = StallingSslObject(handshake_pending=True)
        pipeline, handler, capture, sched = make_pipeline(
            ssl_obj,
            SslIoPipelineHandler.Config(handshake_timeout_s=3.),
        )
        with pipeline:
            pipeline.feed_initial_input()
            timer = sched.single_live()
            self.assertEqual(timer.delay_s, 3.)

            pipeline.feed_in(b'\x00')
            self.assertIs(sched.single_live(), timer)

            timer.fire()

            self.assertEqual(handler.state, SslIoPipelineHandler.State.CLOSED)
            self.assertEqual(len(capture.errors), 1)
            error = capture.errors[0]
            self.assertIsInstance(error.exc, TimeoutIoPipelineError)
            self.assertIsNone(error.direction)
            handler_ref = error.handler
            if handler_ref is None:
                self.fail('Expected timeout handler ref')
            self.assertIs(handler_ref.handler, handler)

            output = pipeline.output.drain()
            self.assertEqual(len(output), 1)
            self.assertIsInstance(output[0], IoPipelineMessages.FinalOutput)

            timer.fire()
            self.assertEqual(len(capture.errors), 1)
            self.assertEqual(pipeline.output.drain(), [])

    def test_handshake_completion_cancels_timeout(self):
        ssl_obj = StallingSslObject(handshake_pending=True)
        pipeline, handler, capture, sched = make_pipeline(
            ssl_obj,
            SslIoPipelineHandler.Config(handshake_timeout_s=3.),
        )
        with pipeline:
            pipeline.feed_initial_input()
            timer = sched.single_live()

            ssl_obj.handshake_pending = False
            pipeline.feed_in(b'\x00')

            self.assertEqual(handler.state, SslIoPipelineHandler.State.ESTABLISHED)
            self.assertTrue(timer.cancelled)
            timer.fire()
            self.assertEqual(capture.errors, [])
            self.assertEqual(pipeline.output.drain(), [])

    def test_shutdown_timeout_releases_original_final_output(self):
        ssl_obj = StallingSslObject(handshake_pending=False)
        pipeline, handler, capture, sched = make_pipeline(
            ssl_obj,
            SslIoPipelineHandler.Config(shutdown_timeout_s=4.),
        )
        with pipeline:
            pipeline.feed_initial_input()
            final_output = IoPipelineMessages.FinalOutput()
            pipeline.feed_in(Close(final_output))
            timer = sched.single_live()
            self.assertEqual(timer.delay_s, 4.)

            timer.fire()

            self.assertEqual(handler.state, SslIoPipelineHandler.State.CLOSED)
            self.assertEqual(len(capture.errors), 1)
            self.assertIsInstance(capture.errors[0].exc, TimeoutIoPipelineError)
            self.assertEqual(pipeline.output.drain(), [final_output])

    def test_shutdown_completion_cancels_timeout(self):
        ssl_obj = StallingSslObject(handshake_pending=False)
        pipeline, handler, capture, sched = make_pipeline(
            ssl_obj,
            SslIoPipelineHandler.Config(shutdown_timeout_s=4.),
        )
        with pipeline:
            pipeline.feed_initial_input()
            final_output = IoPipelineMessages.FinalOutput()
            pipeline.feed_in(Close(final_output))
            timer = sched.single_live()

            ssl_obj.shutdown_pending = False
            pipeline.feed_in(IoPipelineFlowMessages.FlushInput())

            self.assertEqual(handler.state, SslIoPipelineHandler.State.CLOSED)
            self.assertTrue(timer.cancelled)
            self.assertEqual(pipeline.output.drain(), [final_output])
            timer.fire()
            self.assertEqual(capture.errors, [])
            self.assertEqual(pipeline.output.drain(), [])


def make_driver_spec(
        ssl_obj: StallingSslObject,
) -> ta.Tuple[IoPipeline.Spec, SslIoPipelineHandler, CaptureTimeoutIoPipelineHandler]:
    handler = SslIoPipelineHandler(
        ta.cast(ssl.SSLContext, StallingSslContext(ssl_obj)),
        server_side=True,
        config=SslIoPipelineHandler.Config(handshake_timeout_s=.01),
    )
    capture = CaptureTimeoutIoPipelineHandler(output_errors=True)
    return IoPipeline.Spec([handler, capture]), handler, capture


class TestSyncSslIoPipelineHandlerTimeout(unittest.TestCase):
    def test_handshake_timeout(self):
        spec, handler, capture = make_driver_spec(StallingSslObject(handshake_pending=True))
        sock, peer = socket.socketpair()
        with peer:
            driver = SyncSocketIoPipelineDriver(spec, sock)
            try:
                error = driver.next()

                self.assertIsInstance(error, TimeoutIoPipelineError)
                self.assertEqual(handler.state, SslIoPipelineHandler.State.CLOSED)
                self.assertEqual(len(capture.errors), 1)
            finally:
                driver.close()


class TestAsyncioSslIoPipelineHandlerTimeout(AsyncioIsolatedAsyncTestCase):
    async def test_handshake_timeout(self):
        spec, handler, capture = make_driver_spec(StallingSslObject(handshake_pending=True))
        driver = PollAsyncioStreamIoPipelineDriver(spec, asyncio.StreamReader())
        try:
            error = await driver.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(handler.state, SslIoPipelineHandler.State.CLOSED)
            self.assertEqual(len(capture.errors), 1)
        finally:
            await driver.close()
