# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import socket
import ssl
import time
import typing as ta
import unittest
import weakref

from .....lite.check import check
from .....secrets import tempssl
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import FdioPoller
from ....fdio.pollers import SelectFdioPoller
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.fdio import IoPipelineDriverSocketFdioHandler
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
                fn: ta.Callable[..., None],
                with_context: bool,
        ) -> None:
            self.__context_ref = weakref.ref(handler_ref._context)
            self.delay_s = delay_s
            self.fn = fn
            self.with_context = with_context

            self.cancelled = False
            self.done = False

        def cancel(self) -> None:
            self.cancelled = True

        def fire(self) -> None:
            if self.cancelled or self.done:
                return

            self.done = True
            context = self.context
            with context.pipeline.enter():
                if self.with_context:
                    self.fn(context)
                else:
                    self.fn()

        @property
        def context(self) -> IoPipelineHandlerContext:
            return check.not_none(self.__context_ref())

    def __init__(self) -> None:
        super().__init__()

        self.handles: ta.List[ManualSchedulingService.Handle] = []

    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> IoPipelineScheduling.Handle:
        handle = self.Handle(handler_ref, delay_s, fn, False)
        self.handles.append(handle)
        return handle

    def schedule_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> IoPipelineScheduling.Handle:
        handle = self.Handle(handler_ref, delay_s, fn, True)
        self.handles.append(handle)
        return handle

    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        for handle in self.handles:
            if handler_ref is None or handle.context is handler_ref._context:
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


class RecordingSelectFdioPoller(SelectFdioPoller):
    def __init__(self) -> None:
        super().__init__()

        self.timeouts: ta.List[ta.Optional[float]] = []

    def poll(self, timeout: ta.Optional[float]) -> FdioPoller.PollResult:
        self.timeouts.append(timeout)
        return super().poll(timeout)


def drain_socket(sock: socket.socket) -> bytes:
    timeout = sock.gettimeout()
    sock.setblocking(False)
    chunks: ta.List[bytes] = []
    try:
        while True:
            try:
                chunk = sock.recv(64 * 1024)
            except BlockingIOError:
                return b''.join(chunks)
            if not chunk:
                return b''.join(chunks)
            chunks.append(chunk)
    finally:
        sock.settimeout(timeout)


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


class TestFdioSslIoPipelineHandlerTimeout(unittest.TestCase):
    def test_real_tls_handshake_timeout(self) -> None:
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        timeout_s = .05
        handler = SslIoPipelineHandler(
            ssl_ctx,
            server_side=True,
            config=SslIoPipelineHandler.Config(handshake_timeout_s=timeout_s),
        )
        capture = CaptureTimeoutIoPipelineHandler()
        sock, peer = socket.socketpair()
        peer.settimeout(.5)
        poller = RecordingSelectFdioPoller()
        driver = IoPipelineDriverSocketFdioHandler(
            sock,
            ('local', 0),
            IoPipeline.Spec([handler, capture]),
        )
        manager = FdioManager(poller)
        try:
            self.assertIsNone(driver.next(read=False))
            self.assertIs(handler.state, SslIoPipelineHandler.State.HANDSHAKE)
            self.assertIsNotNone(handler._handshake_timeout_handle)
            self.assertIsNotNone(driver.next_deadline())
            self.assertTrue(driver.readable())
            self.assertFalse(driver.writable())
            manager.register(driver)

            start = time.monotonic()
            manager.poll()
            elapsed = time.monotonic() - start

            self.assertGreaterEqual(elapsed, .005)
            self.assertLess(elapsed, .5)
            self.assertEqual(len(poller.timeouts), 1)
            timer_delay = poller.timeouts[0]
            if timer_delay is None:
                self.fail('Expected fdio manager to wait for the TLS handshake deadline')
            self.assertGreaterEqual(timer_delay, 0.)
            self.assertLessEqual(timer_delay, timeout_s)

            self.assertIs(handler.state, SslIoPipelineHandler.State.CLOSED)
            self.assertIsNone(handler._handshake_timeout_handle)
            self.assertEqual(len(capture.errors), 1)
            error = capture.errors[0]
            self.assertIsInstance(error.exc, TimeoutIoPipelineError)
            self.assertIsNone(error.direction)
            handler_ref = check.not_none(error.handler)
            self.assertIs(handler_ref.handler, handler)

            self.assertEqual(peer.recv(1), b'')
            self.assertTrue(driver.closed)
            self.assertFalse(driver.pipeline.is_ready)
            self.assertIsNone(driver.next_deadline())
            self.assertEqual(manager._handlers, {})
        finally:
            driver.close()
            peer.close()
            poller.close()


class TestFdioSslIoPipelineHandlerShutdownTimeout(unittest.TestCase):
    _cert: ta.ClassVar[tempssl.SslCert]

    @classmethod
    def setUpClass(cls) -> None:
        from .....subprocesses import sync as _  # import side-effect installing _DEFAULT_SUBPROCESSES  # noqa

        cls._cert = tempssl.generate_temp_localhost_ssl_cert().cert

    def test_real_tls_shutdown_timeout(self) -> None:
        server_ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ssl_ctx.load_cert_chain(self._cert.cert_file, self._cert.key_file)
        handler = SslIoPipelineHandler(
            server_ssl_ctx,
            server_side=True,
            config=SslIoPipelineHandler.Config(shutdown_timeout_s=.05),
        )
        capture = CaptureTimeoutIoPipelineHandler()
        sock, peer = socket.socketpair()
        peer.settimeout(.5)
        poller = RecordingSelectFdioPoller()
        driver = IoPipelineDriverSocketFdioHandler(
            sock,
            ('local', 0),
            IoPipeline.Spec([handler, capture]),
        )
        manager = FdioManager(poller)

        client_ssl_ctx = ssl.create_default_context(cafile=self._cert.cert_file)
        client_in_bio = ssl.MemoryBIO()
        client_out_bio = ssl.MemoryBIO()
        client_ssl = client_ssl_ctx.wrap_bio(
            client_in_bio,
            client_out_bio,
            server_side=False,
            server_hostname='localhost',
        )

        try:
            self.assertIsNone(driver.next(read=False))
            manager.register(driver)

            client_handshake_done = False
            try:
                client_ssl.do_handshake()
            except ssl.SSLWantReadError:
                pass

            for _ in range(20):
                sent = False
                while client_out_bio.pending:
                    peer.sendall(client_out_bio.read())
                    sent = True
                if sent:
                    manager.poll(timeout=.5)

                if (server_data := drain_socket(peer)):
                    client_in_bio.write(server_data)

                if not client_handshake_done:
                    try:
                        client_ssl.do_handshake()
                    except ssl.SSLWantReadError:
                        pass
                    else:
                        client_handshake_done = True

                if client_handshake_done and handler.state is SslIoPipelineHandler.State.ESTABLISHED:
                    break
            else:
                self.fail((client_handshake_done, handler.state))

            self.assertIsNone(handler._shutdown_timeout_handle)
            self.assertIsNone(driver.next_deadline())

            final_output = IoPipelineMessages.FinalOutput()
            completions: ta.List[bool] = []
            final_output.add_listener(lambda msg: completions.append(msg.is_succeeded()))
            driver.enqueue(Close(final_output))
            self.assertIsNone(driver.next(read=False))

            self.assertIs(handler.state, SslIoPipelineHandler.State.SHUTTING_DOWN)
            self.assertIsNotNone(handler._shutdown_timeout_handle)
            self.assertIsNotNone(driver.next_deadline())
            self.assertFalse(final_output.is_done())

            server_shutdown_data = drain_socket(peer)
            self.assertTrue(server_shutdown_data)
            client_in_bio.write(server_shutdown_data)
            try:
                client_ssl.unwrap()
            except ssl.SSLWantReadError:
                pass
            self.assertGreater(client_out_bio.pending, 0)

            poll_count = len(poller.timeouts)
            start = time.monotonic()
            manager.poll()
            elapsed = time.monotonic() - start

            self.assertGreaterEqual(elapsed, .005)
            self.assertLess(elapsed, .5)
            self.assertEqual(len(poller.timeouts), poll_count + 1)
            timer_delay = poller.timeouts[-1]
            if timer_delay is None:
                self.fail('Expected fdio manager to wait for the TLS shutdown deadline')
            self.assertGreaterEqual(timer_delay, 0.)
            self.assertLessEqual(timer_delay, .05)

            self.assertIs(handler.state, SslIoPipelineHandler.State.CLOSED)
            self.assertIsNone(handler._shutdown_timeout_handle)
            self.assertEqual(len(capture.errors), 1)
            error = capture.errors[0]
            self.assertIsInstance(error.exc, TimeoutIoPipelineError)
            self.assertIn('TLS shutdown timed out', str(error.exc))
            self.assertTrue(final_output.is_succeeded())
            self.assertEqual(completions, [True])

            self.assertEqual(peer.recv(1), b'')
            self.assertTrue(driver.closed)
            self.assertFalse(driver.pipeline.is_ready)
            self.assertIsNone(driver.next_deadline())
            self.assertEqual(manager._handlers, {})
        finally:
            driver.close()
            peer.close()
            poller.close()


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
