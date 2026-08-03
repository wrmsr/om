# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import typing as ta
import unittest

from .....io.pipelines.bytes.buffers import OutboundBytesBufferIoPipelineHandler
from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from .....io.pipelines.flow.stub import StubIoPipelineFlowService
from .....io.pipelines.flow.types import IoPipelineFlowMessages
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....headers import HttpHeaders
from ...requests import FullIoPipelineHttpRequest
from ...requests import IoPipelineHttpRequestBodyData
from ...requests import IoPipelineHttpRequestHead
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..apps.asgi import AsgiIoPipelineHandler
from ..requests import IoPipelineHttpRequestAggregatorDecoder
from ..requests import IoPipelineHttpRequestDecoder
from ..responses import IoPipelineHttpResponseEncoder


##


class PauseOutputOnFirstBodyIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self._paused = False

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)

        if isinstance(msg, IoPipelineHttpResponseBodyData) and not self._paused:
            self._paused = True
            ctx.feed_in(IoPipelineFlowMessages.PauseOutput())


class CaptureOutputWritabilityIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.events: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineFlowMessages.ReadyForOutput, IoPipelineFlowMessages.PauseOutput)):
            self.events.append(msg)
        ctx.feed_in(msg)


class ControlledStreamWriter:
    class Transport:
        def __init__(self) -> None:
            super().__init__()

            self.size = 0
            self.limits: ta.Optional[ta.Tuple[int, int]] = None

        def set_write_buffer_limits(self, *, high: int, low: int) -> None:
            self.limits = (low, high)

        def get_write_buffer_size(self) -> int:
            return self.size

    def __init__(self) -> None:
        super().__init__()

        self.transport = self.Transport()
        self.data = bytearray()
        self.drain_calls = 0
        self.closed = False

        self._drain_started = asyncio.Event()
        self._drain_permits: asyncio.Queue = asyncio.Queue()

    def write(self, data: bytes) -> None:
        self.data.extend(data)
        self.transport.size += len(data)

    async def drain(self) -> None:
        self.drain_calls += 1
        self._drain_started.set()
        await self._drain_permits.get()
        self.transport.size = 0

    async def wait_for_drain(self, n: int) -> None:
        while self.drain_calls < n:
            self._drain_started.clear()
            if self.drain_calls >= n:
                break
            await asyncio.wait_for(self._drain_started.wait(), 1.)

    def allow_drain(self) -> None:
        self._drain_permits.put_nowait(None)

    def close(self) -> None:
        self.closed = True

    async def wait_closed(self) -> None:
        pass


##


class TestAsgiIoPipelineHandler(unittest.TestCase):
    @staticmethod
    def _request() -> FullIoPipelineHttpRequest:
        return FullIoPipelineHttpRequest.simple('localhost', '/')

    def _run_deferred(self, channel: IoPipeline, output: ta.Sequence[ta.Any]) -> None:
        self.assertTrue(output)
        deferred = output[-1]
        self.assertIsInstance(deferred, IoPipelineMessages.Defer)
        channel.run_deferred(deferred)

    def test_response_and_flush_order(self) -> None:
        completed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            completed.append('start')

            await send({
                'type': 'http.response.body',
                'body': b'a',
                'more_body': True,
            })
            completed.append('a')

            await send({
                'type': 'http.response.body',
                'body': b'b',
            })
            completed.append('b')

        channel = IoPipeline.new(
            [AsgiIoPipelineHandler(app)],
            services=[StubIoPipelineFlowService()],
        )

        channel.feed_in(self._request())

        head_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in head_output],
            [
                IoPipelineHttpResponseHead,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(completed, [])

        self._run_deferred(channel, head_output)
        first_body_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in first_body_output],
            [
                IoPipelineHttpResponseBodyData,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(first_body_output[0].data, b'a')
        self.assertEqual(completed, ['start'])

        self._run_deferred(channel, first_body_output)
        final_body_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in final_body_output],
            [
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseEnd,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(final_body_output[0].data, b'b')
        self.assertEqual(completed, ['start', 'a'])

        self._run_deferred(channel, final_body_output)
        final_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in final_output],
            [
                IoPipelineMessages.FinalOutput,
            ],
        )
        self.assertEqual(completed, ['start', 'a', 'b'])

    def test_send_waits_for_output_writability(self) -> None:
        completed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            completed.append('start')

            await send({
                'type': 'http.response.body',
                'body': b'a',
                'more_body': True,
            })
            completed.append('a')

            await send({
                'type': 'http.response.body',
                'body': b'b',
            })
            completed.append('b')

        channel = IoPipeline.new(
            [
                PauseOutputOnFirstBodyIoPipelineHandler(),
                AsgiIoPipelineHandler(app),
            ],
            services=[StubIoPipelineFlowService()],
        )

        channel.feed_in(self._request())

        head_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in head_output],
            [
                IoPipelineHttpResponseHead,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(completed, [])

        self._run_deferred(channel, head_output)
        first_body_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in first_body_output],
            [
                IoPipelineHttpResponseBodyData,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(first_body_output[0].data, b'a')
        self.assertEqual(completed, ['start'])

        self._run_deferred(channel, first_body_output)
        self.assertEqual(channel.output.drain(), [])
        self.assertEqual(completed, ['start', 'a'])

        channel.feed_in(IoPipelineFlowMessages.ReadyForOutput())

        resumed_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in resumed_output],
            [
                IoPipelineHttpResponseBodyData,
                IoPipelineHttpResponseEnd,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(resumed_output[0].data, b'b')
        self.assertEqual(completed, ['start', 'a'])

        self._run_deferred(channel, resumed_output)

        final_output = channel.output.drain()
        self.assertEqual(len(final_output), 1)
        self.assertIsInstance(final_output[0], IoPipelineMessages.FinalOutput)
        self.assertEqual(completed, ['start', 'a', 'b'])

    def test_pause_before_request_blocks_first_send(self) -> None:
        completed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 204,
                'headers': [],
            })
            completed.append('start')

            await send({
                'type': 'http.response.body',
            })
            completed.append('body')

        channel = IoPipeline.new(
            [AsgiIoPipelineHandler(app)],
            services=[StubIoPipelineFlowService()],
        )

        channel.feed_in(IoPipelineFlowMessages.PauseOutput())
        channel.feed_in(self._request())
        self.assertEqual(channel.output.drain(), [])
        self.assertEqual(completed, [])

        channel.feed_in(IoPipelineFlowMessages.ReadyForOutput())
        head_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in head_output],
            [
                IoPipelineHttpResponseHead,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )

        self._run_deferred(channel, head_output)

        body_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in body_output],
            [
                IoPipelineHttpResponseEnd,
                IoPipelineFlowMessages.FlushOutput,
                IoPipelineMessages.Defer,
            ],
        )
        self.assertEqual(completed, ['start'])

        self._run_deferred(channel, body_output)

        final_output = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in final_output],
            [
                IoPipelineMessages.FinalOutput,
            ],
        )
        self.assertEqual(completed, ['start', 'body'])


class TestAsgiDisconnect(unittest.TestCase):
    @staticmethod
    def _head(target: str = '/upload', method: str = 'POST') -> IoPipelineHttpRequestHead:
        return IoPipelineHttpRequestHead(
            method=method,
            target=target,
            headers=HttpHeaders([('Host', 'test')]),
        )

    @staticmethod
    def _new_channel(app: ta.Any) -> IoPipeline:
        return IoPipeline.new(
            [AsgiIoPipelineHandler(app)],
            services=[StubIoPipelineFlowService()],
        )

    def _drain(self, channel: IoPipeline) -> ta.List[ta.Any]:
        out: ta.List[ta.Any] = []
        while True:
            msgs = channel.output.drain()
            if not msgs:
                return out
            for msg in msgs:
                if isinstance(msg, IoPipelineMessages.Defer):
                    channel.run_deferred(msg)
                else:
                    out.append(msg)

    def test_final_input_delivers_disconnect_to_pending_receive(self) -> None:
        events: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            while True:
                event = await receive()
                events.append(event['type'])
                if event['type'] == 'http.disconnect':
                    return
                if not event.get('more_body', False):
                    break

        channel = self._new_channel(app)
        try:
            channel.feed_in(self._head())
            self.assertEqual(self._drain(channel), [])
            self.assertEqual(events, [])

            channel.feed_in(IoPipelineHttpRequestBodyData(b'partial'))
            self.assertEqual(self._drain(channel), [])
            self.assertEqual(events, ['http.request'])

            channel.feed_final_input()
            out = self._drain(channel)

            self.assertEqual(events, ['http.request', 'http.disconnect'])
            self.assertEqual([type(msg) for msg in out], [IoPipelineMessages.FinalOutput])
        finally:
            channel.destroy()

    def test_receive_after_disconnect_reports_disconnect(self) -> None:
        events: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            for _ in range(3):
                events.append((await receive())['type'])

        channel = self._new_channel(app)
        try:
            channel.feed_in(self._head())
            self.assertEqual(self._drain(channel), [])

            channel.feed_final_input()
            out = self._drain(channel)

            self.assertEqual(events, ['http.disconnect'] * 3)
            self.assertEqual([type(msg) for msg in out], [IoPipelineMessages.FinalOutput])
        finally:
            channel.destroy()

    def test_receive_after_response_finished_reports_disconnect(self) -> None:
        events: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [],
            })
            await send({
                'type': 'http.response.body',
                'body': b'ok',
            })

            events.append((await receive())['type'])

        channel = self._new_channel(app)
        try:
            channel.feed_in(FullIoPipelineHttpRequest.simple('localhost', '/'))
            out = self._drain(channel)

            self.assertEqual(events, ['http.disconnect'])
            self.assertEqual(
                [type(msg) for msg in out],
                [
                    IoPipelineHttpResponseHead,
                    IoPipelineFlowMessages.FlushOutput,
                    IoPipelineHttpResponseBodyData,
                    IoPipelineHttpResponseEnd,
                    IoPipelineFlowMessages.FlushOutput,
                    IoPipelineMessages.FinalOutput,
                ],
            )
        finally:
            channel.destroy()

    def test_removal_closes_in_flight_app(self) -> None:
        closed: ta.List[str] = []

        async def app(scope, receive, send):  # noqa
            try:
                await receive()
            except GeneratorExit:
                closed.append('closed')
                raise

        channel = self._new_channel(app)
        try:
            channel.feed_in(self._head())
            self.assertEqual(self._drain(channel), [])
            self.assertEqual(closed, [])
        finally:
            channel.destroy()

        self.assertEqual(closed, ['closed'])


class TestAsgiRequestScope(unittest.TestCase):
    def _run(self, target: str) -> ta.Mapping[str, ta.Any]:
        scopes: ta.List[ta.Mapping[str, ta.Any]] = []

        async def app(scope, receive, send):  # noqa
            scopes.append(scope)

            await send({
                'type': 'http.response.start',
                'status': 204,
                'headers': [],
            })
            await send({
                'type': 'http.response.body',
            })

        channel = IoPipeline.new(
            [AsgiIoPipelineHandler(app)],
            services=[StubIoPipelineFlowService()],
        )
        try:
            channel.feed_in(FullIoPipelineHttpRequest.simple('localhost', target))
            while (msgs := channel.output.drain()):
                for msg in msgs:
                    if isinstance(msg, IoPipelineMessages.Defer):
                        channel.run_deferred(msg)
        finally:
            channel.destroy()

        self.assertEqual(len(scopes), 1)
        return scopes[0]

    def test_path_excludes_query_string(self) -> None:
        scope = self._run('/ping?x=1&y=2')

        self.assertEqual(scope['path'], '/ping')
        self.assertEqual(scope['raw_path'], b'/ping')
        self.assertEqual(scope['query_string'], b'x=1&y=2')

    def test_path_is_percent_decoded(self) -> None:
        scope = self._run('/pi%20ng/%C3%A9?q=a%20b')

        self.assertEqual(scope['path'], '/pi ng/é')
        self.assertEqual(scope['raw_path'], b'/pi%20ng/%C3%A9')
        self.assertEqual(scope['query_string'], b'q=a%20b')

    def test_no_query_string(self) -> None:
        scope = self._run('/ping')

        self.assertEqual(scope['path'], '/ping')
        self.assertEqual(scope['query_string'], b'')


class TestAsgiIoPipelineDriverBackpressure(AsyncioIsolatedAsyncTestCase):
    async def test_slow_writer_bounds_asgi_production(self) -> None:
        attempted: ta.List[str] = []
        completed: ta.List[str] = []
        a_body = b'a' * 64
        b_body = b'b' * 64

        async def app(scope, receive, send):  # noqa
            attempted.append('start')
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [(b'Content-Length', b'128')],
            })
            completed.append('start')

            attempted.append('a')
            await send({
                'type': 'http.response.body',
                'body': a_body,
                'more_body': True,
            })
            completed.append('a')

            attempted.append('b')
            await send({
                'type': 'http.response.body',
                'body': b_body,
            })
            completed.append('b')

        reader = asyncio.StreamReader()
        reader.feed_data(b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n')
        writer = ControlledStreamWriter()
        capture = CaptureOutputWritabilityIoPipelineHandler()
        driver = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    OutboundBytesBufferIoPipelineHandler(
                        OutboundBytesBufferIoPipelineHandler.Config(
                            flush_threshold=None,
                            write_high_watermark=1024 * 1024,
                            write_low_watermark=256 * 1024,
                        ),
                    ),
                    IoPipelineHttpResponseEncoder(),
                    IoPipelineHttpRequestDecoder(),
                    IoPipelineHttpRequestAggregatorDecoder(),
                    capture,
                    AsgiIoPipelineHandler(app),
                ],
                services=[StubIoPipelineFlowService()],
            ),
            reader,
            ta.cast(asyncio.StreamWriter, writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=32,
                write_low_watermark=8,
            ),
        )

        task = asyncio.create_task(driver.loop_until_done())
        try:
            await writer.wait_for_drain(1)
            self.assertEqual(writer.transport.limits, (8, 32))
            self.assertGreater(writer.transport.size, 32)
            self.assertEqual(attempted, ['start'])
            self.assertEqual(completed, [])
            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )

            writer.allow_drain()
            await writer.wait_for_drain(2)
            self.assertGreater(writer.transport.size, 32)
            self.assertEqual(attempted, ['start', 'a'])
            self.assertEqual(completed, ['start'])
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                    IoPipelineFlowMessages.PauseOutput,
                ],
            )

            writer.allow_drain()
            await writer.wait_for_drain(3)
            self.assertGreater(writer.transport.size, 32)
            self.assertEqual(attempted, ['start', 'a', 'b'])
            self.assertEqual(completed, ['start', 'a'])
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                    IoPipelineFlowMessages.PauseOutput,
                ],
            )

            writer.allow_drain()
            await asyncio.wait_for(task, 1.)

            self.assertTrue(writer.closed)
            self.assertEqual(completed, ['start', 'a', 'b'])
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                ],
            )
            self.assertEqual(
                bytes(writer.data),
                (
                    b'HTTP/1.1 200 OK\r\n'
                    b'Content-Length: 128\r\n'
                    b'\r\n' +
                    a_body +
                    b_body
                ),
            )

        finally:
            for _ in range(4):
                writer.allow_drain()
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            await driver.close()
