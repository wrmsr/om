# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
import asyncio
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ....io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from ....io.pipelines.flow.stub import StubIoPipelineFlowService
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...headers import HttpHeaders
from ...versions import HttpVersions
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestAborted
from ..requests import IoPipelineHttpRequestEnd
from ..requests import IoPipelineHttpRequestHead
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseAborted
from ..responses import IoPipelineHttpResponseEnd
from ..responses import IoPipelineHttpResponseHead
from ..servers.keepalive import IoPipelineHttpServerKeepAliveHandler
from ..servers.requests import IoPipelineHttpRequestAggregatorDecoder
from ..servers.requests import IoPipelineHttpRequestDecoder
from ..servers.responses import IoPipelineHttpResponseEncoder


##


class TestKeepAliveDecision(unittest.TestCase):
    def test_invalid_idle_timeout(self) -> None:
        for timeout_s in [0., -1., float('inf'), float('-inf'), float('nan')]:
            with self.subTest(timeout_s=timeout_s):
                with self.assertRaises(ValueError):
                    IoPipelineHttpServerKeepAliveHandler(timeout_s)

    def test_http11_default_keep_alive(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test')]),
            version=HttpVersions.HTTP_1_1,
        )
        self.assertTrue(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))

    def test_http11_connection_close(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test'), ('Connection', 'close')]),
            version=HttpVersions.HTTP_1_1,
        )
        self.assertFalse(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))

    def test_http10_default_close(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test')]),
            version=HttpVersions.HTTP_1_0,
        )
        self.assertFalse(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))

    def test_http10_connection_keep_alive(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test'), ('Connection', 'keep-alive')]),
            version=HttpVersions.HTTP_1_0,
        )
        self.assertTrue(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))

    def test_http11_connection_close_case_insensitive(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test'), ('Connection', 'Close')]),
            version=HttpVersions.HTTP_1_1,
        )
        self.assertFalse(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))

    def test_http11_connection_list_close(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test'), ('Connection', 'TE, Close')]),
            version=HttpVersions.HTTP_1_1,
        )
        self.assertFalse(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))

    def test_http10_connection_list_keep_alive(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/test',
            headers=HttpHeaders([('Host', 'test'), ('Connection', 'Keep-Alive, Upgrade')]),
            version=HttpVersions.HTTP_1_0,
        )
        self.assertTrue(IoPipelineHttpServerKeepAliveHandler.is_request_keep_alive(head))


##


class _SimpleEchoHandler:
    """Test handler that echoes the request target as the response body. Does NOT emit FinalOutput."""

    from ....io.pipelines.core import IoPipelineHandler as _Base

    class Handler(_Base):
        def inbound(self, ctx, msg):
            if isinstance(msg, FullIoPipelineHttpRequest):
                ctx.feed_out(FullIoPipelineHttpResponse(
                    head=IoPipelineHttpResponseHead(
                        status=200,
                        reason='OK',
                        headers=HttpHeaders([
                            ('Content-Length', str(len(msg.head.target))),
                        ]),
                    ),
                    body=msg.head.target.encode(),
                ))
                return

            ctx.feed_in(msg)


_INTERIM_RESPONSE = object()
_RESPONSE_HEAD = object()
_RESPONSE_END = object()
_RESPONSE_ABORTED = object()


def _make_response_head(status, **kwargs):
    return IoPipelineHttpResponseHead(
        status=status,
        reason=IoPipelineHttpResponseHead.get_reason_phrase(status),
        headers=HttpHeaders([]),
        **kwargs,
    )


class _ResponseControlHandler(IoPipelineHandler):
    """Emits controlled response objects in reply to sentinel inbound messages."""

    def __init__(self, *, abort_response_status=None, respond_on_final_input=False) -> None:
        super().__init__()

        self._abort_response_status = abort_response_status
        self._respond_on_final_input = respond_on_final_input

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)
            if self._respond_on_final_input:
                ctx.feed_out(_make_response_head(200))
                ctx.feed_out(IoPipelineHttpResponseEnd())

        elif msg is _INTERIM_RESPONSE:
            ctx.feed_out(_make_response_head(100))
            ctx.feed_out(IoPipelineHttpResponseEnd())

        elif msg is _RESPONSE_HEAD:
            ctx.feed_out(_make_response_head(200))

        elif msg is _RESPONSE_END:
            ctx.feed_out(IoPipelineHttpResponseEnd())

        elif msg is _RESPONSE_ABORTED:
            ctx.feed_out(IoPipelineHttpResponseAborted('aborted'))

        elif isinstance(msg, IoPipelineHttpRequestAborted) and self._abort_response_status is not None:
            ctx.feed_out(FullIoPipelineHttpResponse(
                head=_make_response_head(self._abort_response_status),
                body=b'',
            ))

        elif isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


def _make_control_channel(*, idle_timeout_s=None, **kwargs):
    ka = IoPipelineHttpServerKeepAliveHandler(idle_timeout_s)
    control = _ResponseControlHandler(**kwargs)
    channel = IoPipeline.new([
        ka,
        control,
    ], IoPipeline.Config(inbound_terminal='drop'))
    return ka, channel


def _feed_request_head(channel, *, version=HttpVersions.HTTP_1_1, connection=None):
    channel.feed_in(IoPipelineHttpRequestHead(
        method='POST',
        target='/upload',
        headers=HttpHeaders([
            ('Host', 'test'),
            *([('Connection', connection)] if connection is not None else []),
        ]),
        version=version,
    ))


def _make_ka_channel():
    ka = IoPipelineHttpServerKeepAliveHandler()
    echo = _SimpleEchoHandler.Handler()
    channel = IoPipeline.new([
        ka,
        echo,
    ], IoPipeline.Config(inbound_terminal='drop'))
    return channel


def _make_timed_ka_spec(*handlers):
    return IoPipeline.Spec(
        handlers,
        services=[
            StubIoPipelineFlowService(auto_read=False),
        ],
    )


class TestKeepAliveHandler(unittest.TestCase):
    def test_keep_alive_no_final_output(self) -> None:
        """HTTP/1.1 request without Connection: close should NOT emit FinalOutput."""

        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/ping',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        self.assertEqual(len(out), 1)
        resp = out[0]
        self.assertIsInstance(resp, FullIoPipelineHttpResponse)
        self.assertEqual(resp.body, b'/ping')

    def test_connection_close_emits_final_output(self) -> None:
        """HTTP/1.1 request with Connection: close should emit FinalOutput after response."""

        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/ping',
                headers=HttpHeaders([('Host', 'test'), ('Connection', 'close')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], FullIoPipelineHttpResponse)
        self.assertIsInstance(out[1], IoPipelineMessages.FinalOutput)

    def test_multiple_requests_keep_alive(self) -> None:
        """Multiple HTTP/1.1 requests on same pipeline - no FinalOutput until Connection: close."""

        channel = _make_ka_channel()

        # First request - keep-alive
        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/a',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out1 = channel.output.drain()
        self.assertEqual(len(out1), 1)
        self.assertIsInstance(out1[0], FullIoPipelineHttpResponse)
        self.assertEqual(out1[0].body, b'/a')

        # Second request - keep-alive
        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/b',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out2 = channel.output.drain()
        self.assertEqual(len(out2), 1)
        self.assertIsInstance(out2[0], FullIoPipelineHttpResponse)
        self.assertEqual(out2[0].body, b'/b')

        # Third request - close
        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/c',
                headers=HttpHeaders([('Host', 'test'), ('Connection', 'close')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out3 = channel.output.drain()
        self.assertEqual(len(out3), 2)
        self.assertIsInstance(out3[0], FullIoPipelineHttpResponse)
        self.assertEqual(out3[0].body, b'/c')
        self.assertIsInstance(out3[1], IoPipelineMessages.FinalOutput)

    def test_final_input_while_idle_emits_final_output(self) -> None:
        """FinalInput (client EOF) while idle should emit FinalOutput."""

        channel = _make_ka_channel()

        # First request - keep-alive
        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/a',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))
        channel.output.drain()

        # Client disconnects
        channel.feed_in(IoPipelineMessages.FinalInput())

        out = channel.output.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineMessages.FinalOutput)

    def test_sets_connection_close_header_on_response(self) -> None:
        """When closing, should set Connection: close on HTTP/1.1 response."""

        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/x',
                headers=HttpHeaders([('Host', 'test'), ('Connection', 'close')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        resp = out[0]
        self.assertIsInstance(resp, FullIoPipelineHttpResponse)
        self.assertTrue(resp.head.headers.contains_value('connection', 'close', ignore_case=True))

    def test_http10_default_emits_final_output(self) -> None:
        """HTTP/1.0 without Connection: keep-alive should emit FinalOutput."""

        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/x',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_0,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], FullIoPipelineHttpResponse)
        self.assertIsInstance(out[1], IoPipelineMessages.FinalOutput)


class TestKeepAliveInterimResponses(unittest.TestCase):
    def test_interim_response_is_not_exchange_completion(self) -> None:
        """A 100 Continue must not complete the exchange - the real response must still get through."""

        ka, channel = _make_control_channel()

        _feed_request_head(channel, connection='close')
        channel.output.drain()

        channel.feed_in(_INTERIM_RESPONSE)
        interim = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in interim],
            [IoPipelineHttpResponseHead, IoPipelineHttpResponseEnd],
        )
        self.assertEqual(interim[0].status, 100)
        self.assertFalse(interim[0].headers.lower.get('connection'))
        self.assertFalse(ka._idle)

        channel.feed_in(_RESPONSE_HEAD)
        channel.feed_in(_RESPONSE_END)
        final = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in final],
            [IoPipelineHttpResponseHead, IoPipelineHttpResponseEnd, IoPipelineMessages.FinalOutput],
        )
        self.assertEqual(final[0].status, 200)
        self.assertTrue(final[0].headers.contains_value('connection', 'close', ignore_case=True))

    def test_final_input_during_interim_does_not_take_idle_path(self) -> None:
        """Peer EOF while an interim response is outstanding must let the real response finish, not close outright."""

        ka, channel = _make_control_channel()

        _feed_request_head(channel)
        channel.output.drain()

        channel.feed_in(_INTERIM_RESPONSE)
        channel.output.drain()
        self.assertFalse(ka._idle)

        channel.feed_final_input()

        self.assertFalse(ka._closing)
        self.assertFalse(ka._keep_alive)
        self.assertEqual(channel.output.drain(), [])

    def test_response_after_final_input_during_interim_completes(self) -> None:
        ka, channel = _make_control_channel(respond_on_final_input=True)

        _feed_request_head(channel)
        channel.output.drain()

        channel.feed_in(_INTERIM_RESPONSE)
        channel.output.drain()

        channel.feed_final_input()
        final = channel.output.drain()

        self.assertEqual(
            [type(msg) for msg in final],
            [IoPipelineHttpResponseHead, IoPipelineHttpResponseEnd, IoPipelineMessages.FinalOutput],
        )
        self.assertEqual(final[0].status, 200)
        self.assertTrue(ka._closing)

    def test_interim_response_does_not_rearm_idle_timer(self) -> None:
        keep_alive = IoPipelineHttpServerKeepAliveHandler(60.)
        drv = SyncSocketIoPipelineDriver(
            _make_timed_ka_spec(keep_alive, _ResponseControlHandler()),
            object(),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            self.assertIsNotNone(keep_alive._handle)

            drv.enqueue(IoPipelineHttpRequestHead(
                method='POST',
                target='/upload',
                headers=HttpHeaders([('Host', 'test'), ('Expect', '100-continue')]),
                version=HttpVersions.HTTP_1_1,
            ))
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(keep_alive._handle)

            drv.enqueue(_INTERIM_RESPONSE)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseHead)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseEnd)

            self.assertFalse(keep_alive._idle)
            self.assertIsNone(keep_alive._handle)

            drv.enqueue(_RESPONSE_HEAD, _RESPONSE_END)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseHead)
            self.assertIsInstance(drv.next(read=False), IoPipelineHttpResponseEnd)

            self.assertTrue(keep_alive._idle)
            self.assertIsNotNone(keep_alive._handle)
        finally:
            drv.close()


class TestKeepAliveAborts(unittest.TestCase):
    def test_response_aborted_closes_connection(self) -> None:
        ka, channel = _make_control_channel()

        _feed_request_head(channel)
        channel.output.drain()

        channel.feed_in(_RESPONSE_ABORTED)
        out = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in out],
            [IoPipelineHttpResponseAborted, IoPipelineMessages.FinalOutput],
        )
        self.assertTrue(ka._closing)

    def test_request_aborted_closes_connection(self) -> None:
        _, channel = _make_control_channel()

        _feed_request_head(channel)
        channel.output.drain()

        channel.feed_in(IoPipelineHttpRequestAborted('bad chunk'))
        out = channel.output.drain()
        self.assertEqual([type(msg) for msg in out], [IoPipelineMessages.FinalOutput])

    def test_request_aborted_error_response_closes_connection(self) -> None:
        _, channel = _make_control_channel(abort_response_status=400)

        _feed_request_head(channel)
        channel.output.drain()

        channel.feed_in(IoPipelineHttpRequestAborted('bad chunk'))
        out = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in out],
            [FullIoPipelineHttpResponse, IoPipelineMessages.FinalOutput],
        )
        self.assertTrue(out[0].head.headers.contains_value('connection', 'close', ignore_case=True))


class TestKeepAliveConnectionHeaderVersion(unittest.TestCase):
    def test_http10_keep_alive_is_echoed(self) -> None:
        """An HTTP/1.0 keep-alive request must get `Connection: keep-alive` back on an HTTP/1.1-built response."""

        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/x',
                headers=HttpHeaders([('Host', 'test'), ('Connection', 'keep-alive')]),
                version=HttpVersions.HTTP_1_0,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        self.assertEqual([type(msg) for msg in out], [FullIoPipelineHttpResponse])
        self.assertTrue(out[0].head.headers.contains_value('connection', 'keep-alive', ignore_case=True))

    def test_http11_keep_alive_is_not_stamped(self) -> None:
        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/x',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_1,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        self.assertEqual(len(out), 1)
        self.assertFalse(out[0].head.headers.lower.get('connection'))

    def test_http10_close_is_stated_explicitly(self) -> None:
        channel = _make_ka_channel()

        channel.feed_in(FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/x',
                headers=HttpHeaders([('Host', 'test')]),
                version=HttpVersions.HTTP_1_0,
            ),
            body=b'',
        ))

        out = channel.output.drain()
        self.assertEqual(
            [type(msg) for msg in out],
            [FullIoPipelineHttpResponse, IoPipelineMessages.FinalOutput],
        )
        self.assertTrue(out[0].head.headers.contains_value('connection', 'close', ignore_case=True))


class TestSyncKeepAliveIdleTimeout(unittest.TestCase):
    def test_expires_while_waiting_for_first_request(self) -> None:
        keep_alive = IoPipelineHttpServerKeepAliveHandler(.01)
        drv = SyncSocketIoPipelineDriver(_make_timed_ka_spec(keep_alive), object())
        try:
            self.assertIsNone(drv.next())

            self.assertFalse(drv.is_running)
            self.assertIsNone(keep_alive._handle)
        finally:
            drv.close()

    def test_cancels_while_request_is_active(self) -> None:
        keep_alive = IoPipelineHttpServerKeepAliveHandler(60.)
        requests = InboundQueueIoPipelineHandler(filter_type=FullIoPipelineHttpRequest)
        drv = SyncSocketIoPipelineDriver(_make_timed_ka_spec(keep_alive, requests), object())
        try:
            self.assertIsNone(drv.next(read=False))
            self.assertIsNotNone(keep_alive._handle)

            drv.enqueue(FullIoPipelineHttpRequest(
                head=IoPipelineHttpRequestHead(
                    method='GET',
                    target='/active',
                    headers=HttpHeaders([('Host', 'test')]),
                    version=HttpVersions.HTTP_1_1,
                ),
                body=b'',
            ))
            self.assertIsNone(drv.next(read=False))

            self.assertIsNone(keep_alive._handle)
            self.assertIsNone(drv._sched.next_delay())
            self.assertEqual(len(requests.drain()), 1)
        finally:
            drv.close()

    def test_rearms_after_response_completion(self) -> None:
        keep_alive = IoPipelineHttpServerKeepAliveHandler(60.)
        drv = SyncSocketIoPipelineDriver(
            _make_timed_ka_spec(keep_alive, _SimpleEchoHandler.Handler()),
            object(),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            first_handle = keep_alive._handle
            self.assertIsNotNone(first_handle)

            drv.enqueue(FullIoPipelineHttpRequest(
                head=IoPipelineHttpRequestHead(
                    method='GET',
                    target='/complete',
                    headers=HttpHeaders([('Host', 'test')]),
                    version=HttpVersions.HTTP_1_1,
                ),
                body=b'',
            ))
            response = drv.next(read=False)

            self.assertIsInstance(response, FullIoPipelineHttpResponse)
            self.assertIsNotNone(keep_alive._handle)
            self.assertIsNot(keep_alive._handle, first_handle)
        finally:
            drv.close()


class TestAsyncioKeepAliveIdleTimeout(AsyncioIsolatedAsyncTestCase):
    async def test_expires_while_waiting_for_first_request(self) -> None:
        keep_alive = IoPipelineHttpServerKeepAliveHandler(.01)
        drv = PollAsyncioStreamIoPipelineDriver(
            _make_timed_ka_spec(keep_alive),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next())

            self.assertFalse(drv.pipeline.is_ready)
            self.assertIsNone(keep_alive._handle)
        finally:
            await drv.close()


##


class TestDecoderMultiMessage(unittest.TestCase):
    def test_decoder_parses_two_messages(self) -> None:
        """Decoder should parse multiple HTTP messages from a single byte stream."""

        decoder = IoPipelineHttpRequestDecoder()
        channel = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ], IoPipeline.Config(inbound_terminal='drop'))

        wire = (
            b'GET /first HTTP/1.1\r\nHost: test\r\n\r\n'
            b'GET /second HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n'
        )
        channel.feed_in(wire)

        out = ibq.drain()

        heads = [m for m in out if isinstance(m, IoPipelineHttpRequestHead)]
        ends = [m for m in out if isinstance(m, IoPipelineHttpRequestEnd)]
        self.assertEqual(len(heads), 2)
        self.assertEqual(len(ends), 2)
        self.assertEqual(heads[0].target, '/first')
        self.assertEqual(heads[1].target, '/second')

    def test_decoder_parses_two_messages_with_bodies(self) -> None:
        """Decoder should parse multiple HTTP messages with Content-Length bodies."""

        decoder = IoPipelineHttpRequestDecoder()
        channel = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ], IoPipeline.Config(inbound_terminal='drop'))

        wire = (
            b'POST /a HTTP/1.1\r\nHost: test\r\nContent-Length: 5\r\n\r\nhello'
            b'POST /b HTTP/1.1\r\nHost: test\r\nContent-Length: 5\r\n\r\nworld'
        )
        channel.feed_in(wire)

        out = ibq.drain()
        heads = [m for m in out if isinstance(m, IoPipelineHttpRequestHead)]
        self.assertEqual(len(heads), 2)
        self.assertEqual(heads[0].target, '/a')
        self.assertEqual(heads[1].target, '/b')


##


class TestKeepAliveFullPipeline(unittest.TestCase):
    def test_full_pipeline_two_requests(self) -> None:
        """Full pipeline: Decoder -> Aggregator -> KeepAlive -> Echo, two requests on same connection."""

        echo = _SimpleEchoHandler.Handler()
        channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestAggregatorDecoder(),
            IoPipelineHttpResponseEncoder(),
            IoPipelineHttpServerKeepAliveHandler(),
            echo,
        ], IoPipeline.Config(inbound_terminal='drop'))

        # First request
        channel.feed_in(b'GET /first HTTP/1.1\r\nHost: test\r\n\r\n')

        out1 = channel.output.drain()
        wire1 = b''.join(m for m in out1 if isinstance(m, bytes))
        self.assertIn(b'HTTP/1.1 200 OK\r\n', wire1)
        self.assertIn(b'/first', wire1)
        self.assertFalse(any(isinstance(m, IoPipelineMessages.FinalOutput) for m in out1))

        # Second request with Connection: close
        channel.feed_in(b'GET /second HTTP/1.1\r\nHost: test\r\nConnection: close\r\n\r\n')

        out2 = channel.output.drain()
        self.assertIsInstance(out2[-1], IoPipelineMessages.FinalOutput)
        wire2 = b''.join(m for m in out2 if isinstance(m, bytes))
        self.assertIn(b'/second', wire2)
        self.assertIn(b'Connection: close\r\n', wire2)

    def test_full_pipeline_final_input_closes(self) -> None:
        """Full pipeline: client EOF after keep-alive request should close connection."""

        echo = _SimpleEchoHandler.Handler()
        channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestAggregatorDecoder(),
            IoPipelineHttpResponseEncoder(),
            IoPipelineHttpServerKeepAliveHandler(),
            echo,
        ], IoPipeline.Config(inbound_terminal='drop'))

        channel.feed_in(b'GET /test HTTP/1.1\r\nHost: test\r\n\r\n')
        channel.output.drain()

        channel.feed_final_input()

        out = channel.output.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineMessages.FinalOutput)
