# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import asyncio
import ssl
import typing as ta
import zlib

from .....io.pipelines.bytes.buffers import OutboundBytesBufferIoPipelineHandler
from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from .....io.pipelines.drivers.types import IoPipelineDriverState
from .....io.pipelines.errors import TimeoutIoPipelineError
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.flow.types import IoPipelineFlow
from .....io.pipelines.flow.types import IoPipelineFlowMessages
from .....io.pipelines.ssl.handlers import SslIoPipelineHandler
from .....io.streambufs.utils import ByteStreamBuffers
from .....lite.check import check
from .....secrets import tempssl
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....headers import HttpHeaders
from ....versions import HttpVersions
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..apps.asgi import AsgiIoPipelineHandler
from ..requests import IoPipelineHttpRequestAggregatorDecoder
from ..requests import IoPipelineHttpRequestDecoder
from ..responses import IoPipelineHttpResponseChunker
from ..responses import IoPipelineHttpResponseCompressor
from ..responses import IoPipelineHttpResponseEncoder
from ..timeouts import IoPipelineHttpServerRequestTimeoutHandler


##


class _PairedControlledStreamWriter:
    class Transport:
        def __init__(self, owner: '_PairedControlledStreamWriter') -> None:
            super().__init__()

            self._owner = owner
            self.limits: ta.Optional[ta.Tuple[int, int]] = None

        def set_write_buffer_limits(self, *, high: int, low: int) -> None:
            self.limits = (low, high)

        def get_write_buffer_size(self) -> int:
            return self._owner.buffer_size

        def abort(self) -> None:
            self._owner.abort()

    def __init__(self, peer_reader: asyncio.StreamReader) -> None:
        super().__init__()

        self.transport = self.Transport(self)
        self._peer_reader = peer_reader
        self._pending = bytearray()

        self.auto_drain = True
        self.drain_calls = 0
        self.max_buffer_size = 0
        self.closed = False
        self.aborted = False
        self.closed_with_pending = False

        self._drain_started = asyncio.Event()
        self._drain_permits: asyncio.Queue = asyncio.Queue()
        self._fed_eof = False

    def write(self, data: bytes) -> None:
        self._pending.extend(data)
        self.max_buffer_size = max(self.max_buffer_size, len(self._pending))

    @property
    def buffer_size(self) -> int:
        return len(self._pending)

    def _flush(self) -> None:
        if not self._pending:
            return
        data = bytes(self._pending)
        self._pending.clear()
        self._peer_reader.feed_data(data)

    async def drain(self) -> None:
        self.drain_calls += 1
        self._drain_started.set()
        if not self.auto_drain:
            await self._drain_permits.get()
        self._flush()

    async def wait_for_drain(self, count: int) -> None:
        while self.drain_calls < count:
            self._drain_started.clear()
            if self.drain_calls >= count:
                break
            await asyncio.wait_for(self._drain_started.wait(), 1.)

    def allow_drain(self) -> None:
        self._drain_permits.put_nowait(None)

    def reset_max_buffer_size(self) -> None:
        self.max_buffer_size = len(self._pending)

    def _feed_eof(self) -> None:
        if not self._fed_eof:
            self._fed_eof = True
            self._peer_reader.feed_eof()

    def close(self) -> None:
        self.closed = True
        if self._pending:
            self.closed_with_pending = True
            self._flush()
        self._feed_eof()

    async def wait_closed(self) -> None:
        pass

    def abort(self) -> None:
        self.aborted = True
        self.closed = True
        self._pending.clear()
        self._feed_eof()


class _CaptureOutputWritabilityIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.events: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineFlowMessages.ReadyForOutput, IoPipelineFlowMessages.PauseOutput)):
            self.events.append(msg)
        ctx.feed_in(msg)


class _RawTlsHttpClientIoPipelineHandler(IoPipelineHandler):
    def __init__(self, request: bytes) -> None:
        super().__init__()

        self._request = request
        self.response = bytearray()
        self.input_flushes = 0

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self._request)
            IoPipelineFlow.maybe_flush_output(ctx)
            IoPipelineFlow.maybe_ready_for_input(ctx)

        elif ByteStreamBuffers.can_bytes(msg):
            for mv in ByteStreamBuffers.iter_segments(msg):
                self.response.extend(mv)

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self.input_flushes += 1
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)
            ctx.feed_final_output()

        elif isinstance(msg, IoPipelineMessages.Error):
            raise msg.exc

        else:
            ctx.feed_in(msg)


class _TimeoutResponseIoPipelineHandler(IoPipelineHandler):
    def __init__(self, timeout_seen: asyncio.Event, body_chunks: ta.Iterable[bytes]) -> None:
        super().__init__()

        self._timeout_seen = timeout_seen
        self._body_chunks = list(body_chunks)
        self._next_chunk = 0

        self._active = False
        self._output_writable = True
        self.finished = False

    def _pump(self, ctx: IoPipelineHandlerContext) -> None:
        if not self._active or not self._output_writable or self.finished:
            return

        if self._next_chunk == 0:
            ctx.feed_out(IoPipelineHttpResponseHead(
                status=504,
                reason='Gateway Timeout',
                version=HttpVersions.HTTP_1_1,
                headers=HttpHeaders([
                    ('Content-Encoding', 'gzip'),
                    ('Transfer-Encoding', 'chunked'),
                    ('Connection', 'close'),
                ]),
            ))

        ctx.feed_out(IoPipelineHttpResponseBodyData(self._body_chunks[self._next_chunk]))
        self._next_chunk += 1

        if self._next_chunk == len(self._body_chunks):
            ctx.feed_out(IoPipelineHttpResponseEnd())
            self.finished = True

        IoPipelineFlow.maybe_flush_output(ctx)

        if self.finished:
            ctx.feed_final_output()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error) and isinstance(msg.exc, TimeoutIoPipelineError):
            self._active = True
            self._timeout_seen.set()
            self._pump(ctx)

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self._output_writable = False
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self._output_writable = True
            self._pump(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


##


class TestBackpressureIntegration(AsyncioIsolatedAsyncTestCase):
    _cert: ta.ClassVar[tempssl.SslCert]

    @classmethod
    def setUpClass(cls) -> None:
        from .....subprocesses import sync as _  # import side-effect installing _DEFAULT_SUBPROCESSES  # noqa

        cls._cert = tempssl.generate_temp_localhost_ssl_cert().cert

    @staticmethod
    def _decode_chunked(body: bytes) -> bytes:
        chunks: ta.List[bytes] = []
        pos = 0

        while True:
            line_end = body.index(b'\r\n', pos)
            size = int(body[pos:line_end], 16)
            pos = line_end + 2

            if not size:
                if body[pos:] != b'\r\n':
                    raise AssertionError(body[pos:])
                return b''.join(chunks)

            chunks.append(body[pos:pos + size])
            pos += size
            if body[pos:pos + 2] != b'\r\n':
                raise AssertionError(body[pos:pos + 2])
            pos += 2

    async def test_manual_read_slow_tls_chunked_gzip_response(self) -> None:
        server_ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ssl_ctx.load_cert_chain(self._cert.cert_file, self._cert.key_file)
        client_ssl_ctx = ssl.create_default_context(cafile=self._cert.cert_file)

        request_received = asyncio.Event()
        release_response = asyncio.Event()
        attempted: ta.List[str] = []
        completed: ta.List[str] = []
        body_chunks = [
            bytes(range(64)),
            bytes(range(64, 128)),
            bytes(range(128, 192)),
            bytes(range(192, 256)),
        ]

        async def app(scope, receive, send):  # noqa
            request_received.set()
            await release_response.wait()

            attempted.append('start')
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [
                    (b'content-encoding', b'gzip'),
                    (b'transfer-encoding', b'chunked'),
                    (b'connection', b'close'),
                ],
            })
            completed.append('start')

            for i, chunk in enumerate(body_chunks):
                label = f'body-{i}'
                attempted.append(label)
                await send({
                    'type': 'http.response.body',
                    'body': chunk,
                    'more_body': i < len(body_chunks) - 1,
                })
                completed.append(label)

        server_reader = asyncio.StreamReader()
        client_reader = asyncio.StreamReader()
        server_writer = _PairedControlledStreamWriter(client_reader)
        client_writer = _PairedControlledStreamWriter(server_reader)

        outer_buffer = OutboundBytesBufferIoPipelineHandler(
            OutboundBytesBufferIoPipelineHandler.Config(
                flush_threshold=None,
                write_high_watermark=128,
                write_low_watermark=32,
            ),
        )
        server_ssl = SslIoPipelineHandler(
            server_ssl_ctx,
            server_side=True,
            config=SslIoPipelineHandler.Config(
                write_high_watermark=128,
                write_low_watermark=32,
            ),
        )
        chunker = IoPipelineHttpResponseChunker(
            max_chunk_size=64,
            write_high_watermark=128,
            write_low_watermark=32,
        )
        capture = _CaptureOutputWritabilityIoPipelineHandler()

        server_driver = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    outer_buffer,
                    server_ssl,
                    IoPipelineHttpRequestDecoder(),
                    IoPipelineHttpRequestAggregatorDecoder(),
                    IoPipelineHttpResponseEncoder(),
                    chunker,
                    IoPipelineHttpResponseCompressor(),
                    capture,
                    AsgiIoPipelineHandler(app),
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            server_reader,
            ta.cast(asyncio.StreamWriter, server_writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(
                strict_input_flow=True,
                write_high_watermark=1,
                write_low_watermark=0,
            ),
        )

        client_handler = _RawTlsHttpClientIoPipelineHandler(
            b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n',
        )
        client_driver = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    OutboundBytesBufferIoPipelineHandler(),
                    SslIoPipelineHandler(
                        client_ssl_ctx,
                        server_side=False,
                        server_hostname='localhost',
                    ),
                    client_handler,
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            client_reader,
            ta.cast(asyncio.StreamWriter, client_writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(
                strict_input_flow=True,
                write_high_watermark=1,
                write_low_watermark=0,
            ),
        )

        server_task = asyncio.create_task(server_driver.loop_until_done())
        client_task = asyncio.create_task(client_driver.loop_until_done())
        try:
            await asyncio.wait_for(request_received.wait(), 2.)
            for _ in range(3):
                await asyncio.sleep(0)

            self.assertEqual(server_writer.buffer_size, 0)
            capture.events.clear()
            server_writer.reset_max_buffer_size()
            server_writer.auto_drain = False
            first_blocked_drain = server_writer.drain_calls + 1
            release_response.set()

            labels = ['start', 'body-0', 'body-1', 'body-2', 'body-3']
            blocked_drains = 0
            while True:
                try:
                    await server_writer.wait_for_drain(first_blocked_drain + blocked_drains)
                except TimeoutError:
                    raise AssertionError({
                        'attempted': attempted,
                        'completed': completed,
                        'drain_calls': server_writer.drain_calls,
                        'events': [type(event).__name__ for event in capture.events],
                        'pending': server_writer.buffer_size,
                        'outer_writable': (
                            outer_buffer._downstream_writable,  # noqa
                            outer_buffer._self_writable,  # noqa
                            outer_buffer._announced_writable,  # noqa
                            outer_buffer.outbound_buffered_bytes(),
                        ),
                        'ssl_writable': (
                            server_ssl._transport_writable,  # noqa
                            server_ssl._self_writable,  # noqa
                            server_ssl._announced_writable,  # noqa
                        ),
                        'chunker_writable': (
                            chunker._downstream_writable,  # noqa
                            chunker._self_writable,  # noqa
                            chunker._announced_writable,  # noqa
                        ),
                        'server_done': server_task.done(),
                        'client_done': client_task.done(),
                    }) from None

                blocked_drains += 1
                self.assertLess(blocked_drains, 32)
                self.assertEqual(attempted, labels[:len(attempted)])
                self.assertEqual(completed, labels[:len(completed)])
                self.assertLessEqual(len(completed), len(attempted))
                self.assertLessEqual(len(attempted), len(completed) + 1)
                self.assertGreater(server_writer.buffer_size, 1)
                self.assertEqual(outer_buffer.outbound_buffered_bytes(), 0)
                self.assertLessEqual(check.not_none(server_ssl.outbound_buffered_bytes()), 512)
                self.assertEqual(chunker.outbound_buffered_bytes(), 0)
                event_types = [type(event) for event in capture.events]
                self.assertGreaterEqual(len(event_types), blocked_drains * 2 - 1)
                self.assertEqual(
                    event_types,
                    [
                        IoPipelineFlowMessages.PauseOutput
                        if i % 2 == 0 else IoPipelineFlowMessages.ReadyForOutput
                        for i in range(len(event_types))
                    ],
                )
                self.assertIs(event_types[-1], IoPipelineFlowMessages.PauseOutput)

                closing = completed == labels
                server_writer.allow_drain()
                if closing:
                    break

            self.assertEqual(attempted, labels)
            self.assertEqual(completed, labels)
            self.assertEqual(server_driver.state, IoPipelineDriverState.RUNNING)

            await asyncio.wait_for(asyncio.gather(server_task, client_task), 2.)

            self.assertEqual(server_driver.state, IoPipelineDriverState.CLOSED)
            self.assertEqual(client_driver.state, IoPipelineDriverState.CLOSED)
            self.assertTrue(server_writer.closed)
            self.assertTrue(client_writer.closed)
            self.assertFalse(server_writer.aborted)
            self.assertFalse(client_writer.aborted)
            self.assertFalse(server_writer.closed_with_pending)
            self.assertFalse(client_writer.closed_with_pending)
            self.assertLess(server_writer.max_buffer_size, 2048)
            self.assertGreater(client_handler.input_flushes, 1)
            event_types = [type(event) for event in capture.events]
            self.assertEqual(len(event_types) % 2, 0)
            self.assertEqual(
                event_types,
                [
                    IoPipelineFlowMessages.PauseOutput
                    if i % 2 == 0 else IoPipelineFlowMessages.ReadyForOutput
                    for i in range(len(event_types))
                ],
            )

            response_head, encoded_body = bytes(client_handler.response).split(b'\r\n\r\n', 1)
            self.assertIn(b'content-encoding: gzip', response_head.lower())
            self.assertIn(b'transfer-encoding: chunked', response_head.lower())
            compressed_body = self._decode_chunked(encoded_body)
            self.assertEqual(
                zlib.decompress(compressed_body, 16 + zlib.MAX_WBITS),
                b''.join(body_chunks),
            )

        finally:
            server_writer.auto_drain = True
            for _ in range(16):
                server_writer.allow_drain()
                client_writer.allow_drain()
            for task in (server_task, client_task):
                if not task.done():
                    task.cancel()
            await asyncio.gather(server_task, client_task, return_exceptions=True)
            await server_driver.close()
            await client_driver.close()

    async def test_timeout_response_drains_through_slow_tls_gzip_output(self) -> None:
        server_ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ssl_ctx.load_cert_chain(self._cert.cert_file, self._cert.key_file)
        client_ssl_ctx = ssl.create_default_context(cafile=self._cert.cert_file)

        request_received = asyncio.Event()
        timeout_seen = asyncio.Event()
        pending = asyncio.get_running_loop().create_future()

        async def app(scope, receive, send):  # noqa
            request_received.set()
            await pending

        body_chunks = [bytes((i + j) % 256 for i in range(1024)) for j in range(4)]
        timeout_response = _TimeoutResponseIoPipelineHandler(timeout_seen, body_chunks)
        capture = _CaptureOutputWritabilityIoPipelineHandler()

        server_reader = asyncio.StreamReader()
        client_reader = asyncio.StreamReader()
        server_writer = _PairedControlledStreamWriter(client_reader)
        client_writer = _PairedControlledStreamWriter(server_reader)

        outer_buffer = OutboundBytesBufferIoPipelineHandler(
            OutboundBytesBufferIoPipelineHandler.Config(
                flush_threshold=None,
                write_high_watermark=128,
                write_low_watermark=32,
            ),
        )
        server_ssl = SslIoPipelineHandler(
            server_ssl_ctx,
            server_side=True,
            config=SslIoPipelineHandler.Config(
                write_high_watermark=128,
                write_low_watermark=32,
            ),
        )
        chunker = IoPipelineHttpResponseChunker(
            max_chunk_size=64,
            write_high_watermark=128,
            write_low_watermark=32,
        )

        server_driver = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    outer_buffer,
                    server_ssl,
                    IoPipelineHttpRequestDecoder(),
                    IoPipelineHttpRequestAggregatorDecoder(),
                    IoPipelineHttpResponseEncoder(),
                    chunker,
                    IoPipelineHttpResponseCompressor(),
                    IoPipelineHttpServerRequestTimeoutHandler(.05),
                    capture,
                    AsgiIoPipelineHandler(app),
                    timeout_response,
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            server_reader,
            ta.cast(asyncio.StreamWriter, server_writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(
                strict_input_flow=True,
                write_high_watermark=1,
                write_low_watermark=0,
            ),
        )

        client_handler = _RawTlsHttpClientIoPipelineHandler(
            b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n',
        )
        client_driver = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    OutboundBytesBufferIoPipelineHandler(),
                    SslIoPipelineHandler(
                        client_ssl_ctx,
                        server_side=False,
                        server_hostname='localhost',
                    ),
                    client_handler,
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            client_reader,
            ta.cast(asyncio.StreamWriter, client_writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(
                strict_input_flow=True,
                write_high_watermark=1,
                write_low_watermark=0,
            ),
        )

        server_task = asyncio.create_task(server_driver.loop_until_done())
        client_task = asyncio.create_task(client_driver.loop_until_done())
        try:
            await asyncio.wait_for(request_received.wait(), 2.)
            for _ in range(3):
                await asyncio.sleep(0)

            self.assertEqual(server_writer.buffer_size, 0)
            capture.events.clear()
            server_writer.reset_max_buffer_size()
            server_writer.auto_drain = False
            first_blocked_drain = server_writer.drain_calls + 1

            await asyncio.wait_for(timeout_seen.wait(), 1.)
            if not pending.done():
                pending.set_result(None)
            await server_writer.wait_for_drain(first_blocked_drain)

            self.assertFalse(timeout_response.finished)
            self.assertFalse(server_writer.closed)
            self.assertGreater(server_writer.buffer_size, 1)
            self.assertEqual(outer_buffer.outbound_buffered_bytes(), 0)
            self.assertLessEqual(check.not_none(server_ssl.outbound_buffered_bytes()), 512)
            self.assertEqual(chunker.outbound_buffered_bytes(), 0)

            while not timeout_response.finished:
                drain_calls = server_writer.drain_calls
                server_writer.allow_drain()
                await server_writer.wait_for_drain(drain_calls + 1)

            self.assertFalse(server_writer.closed)
            self.assertGreater(server_writer.buffer_size, 1)
            self.assertIn(server_driver.state, (IoPipelineDriverState.RUNNING, IoPipelineDriverState.DRAINING))

            event_types = [type(event) for event in capture.events]
            self.assertGreaterEqual(len(event_types), 4)
            self.assertEqual(
                event_types,
                [
                    IoPipelineFlowMessages.PauseOutput
                    if i % 2 == 0 else IoPipelineFlowMessages.ReadyForOutput
                    for i in range(len(event_types))
                ],
            )
            self.assertIs(event_types[-1], IoPipelineFlowMessages.PauseOutput)

            server_writer.auto_drain = True
            server_writer.allow_drain()
            await asyncio.wait_for(asyncio.gather(server_task, client_task), 2.)

            self.assertEqual(server_driver.state, IoPipelineDriverState.CLOSED)
            self.assertEqual(client_driver.state, IoPipelineDriverState.CLOSED)
            self.assertTrue(server_writer.closed)
            self.assertTrue(client_writer.closed)
            self.assertFalse(server_writer.aborted)
            self.assertFalse(client_writer.aborted)
            self.assertFalse(server_writer.closed_with_pending)
            self.assertFalse(client_writer.closed_with_pending)

            response_head, encoded_body = bytes(client_handler.response).split(b'\r\n\r\n', 1)
            self.assertIn(b'504 Gateway Timeout', response_head)
            self.assertIn(b'content-encoding: gzip', response_head.lower())
            self.assertIn(b'transfer-encoding: chunked', response_head.lower())
            compressed_body = self._decode_chunked(encoded_body)
            self.assertEqual(
                zlib.decompress(compressed_body, 16 + zlib.MAX_WBITS),
                b''.join(body_chunks),
            )

        finally:
            if not pending.done():
                pending.set_result(None)
            server_writer.auto_drain = True
            for _ in range(16):
                server_writer.allow_drain()
                client_writer.allow_drain()
            for task in (server_task, client_task):
                if not task.done():
                    task.cancel()
            await asyncio.gather(server_task, client_task, return_exceptions=True)
            await server_driver.close()
            await client_driver.close()
