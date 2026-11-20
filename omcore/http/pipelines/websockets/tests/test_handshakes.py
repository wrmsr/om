# ruff: noqa: UP006 UP007 UP045
# @om-lite
import gc
import typing as ta
import unittest
import weakref

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from .....io.streambufs.utils import ByteStreamBuffers
from ....headers import HttpHeaders
from ...requests import FullIoPipelineHttpRequest
from ...requests import IoPipelineHttpRequestHead
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ...servers.requests import IoPipelineHttpRequestDecoder
from ...servers.responses import IoPipelineHttpResponseEncoder
from ..frames import IoPipelineWebsocketFrameDecoder
from ..frames import IoPipelineWebsocketFrameEncoder
from ..handshakes import IoPipelineWebsocketClientUpgradeHandler
from ..handshakes import IoPipelineWebsocketHandshakes
from ..handshakes import IoPipelineWebsocketServerUpgradeHandler
from ..objects import IoPipelineWebsocketFrame
from ..objects import IoPipelineWebsocketOpcode
from ..objects import IoPipelineWebsocketOpen
from ..objects import IoPipelineWebsocketText


SAMPLE_KEY = 'dGhlIHNhbXBsZSBub25jZQ=='
SAMPLE_ACCEPT = 's3pPLMBiTxaQ9kYGzzhZRbK+xOo='


def _upgrade_headers(*extra):
    return HttpHeaders([
        ('Host', 'localhost'),
        ('Upgrade', 'websocket'),
        ('Sec-Websocket-Version', '13'),
        ('Sec-Websocket-Key', SAMPLE_KEY),
        *extra,
    ])


class TestServerUpgradeHandler(unittest.TestCase):
    def _run(self, msg, **kwargs):
        handler = IoPipelineWebsocketServerUpgradeHandler(**kwargs)
        pipeline = IoPipeline.new([
            handler,
            ibq := InboundQueueIoPipelineHandler(),
        ])
        pipeline.feed_in(msg)
        return pipeline, ibq

    def test_accepts_list_valued_connection_header(self) -> None:
        # `Connection: keep-alive, Upgrade` is RFC-legal and what firefox sends.
        pipeline, ibq = self._run(IoPipelineHttpRequestHead(
            method='GET',
            target='/ws',
            headers=_upgrade_headers(('Connection', 'keep-alive, Upgrade')),
        ))

        [resp] = [m for m in pipeline.output.drain() if isinstance(m, IoPipelineHttpResponseHead)]
        assert resp.status == 101
        assert resp.headers.single['Sec-Websocket-Accept'] == SAMPLE_ACCEPT

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)

    def test_accepts_connection_header_split_across_lines(self) -> None:
        pipeline, ibq = self._run(IoPipelineHttpRequestHead(
            method='GET',
            target='/ws',
            headers=_upgrade_headers(
                ('Connection', 'keep-alive'),
                ('Connection', 'Upgrade'),
            ),
        ))

        [resp] = [m for m in pipeline.output.drain() if isinstance(m, IoPipelineHttpResponseHead)]
        assert resp.status == 101

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)

    def test_ignores_non_upgrade_request(self) -> None:
        head = IoPipelineHttpRequestHead(
            method='GET',
            target='/',
            headers=HttpHeaders([('Host', 'localhost'), ('Connection', 'keep-alive')]),
        )
        pipeline, ibq = self._run(head)

        assert ibq.drain() == [head]
        assert pipeline.output.drain() == []

    def test_forwards_non_upgrade_full_request_intact(self) -> None:
        # A non-upgrade Full must not be unwrapped to its head - that silently discards the body and the end.
        full = FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='POST',
                target='/api',
                headers=HttpHeaders([('Host', 'localhost'), ('Content-Length', '11')]),
            ),
            body=b'hello world',
        )
        pipeline, ibq = self._run(full)

        [got] = ibq.drain()
        assert got is full
        assert pipeline.output.drain() == []

    def test_upgrades_full_request(self) -> None:
        full = FullIoPipelineHttpRequest(
            head=IoPipelineHttpRequestHead(
                method='GET',
                target='/ws',
                headers=_upgrade_headers(('Connection', 'Upgrade')),
            ),
            body=b'',
        )
        pipeline, ibq = self._run(full)

        [resp] = [m for m in pipeline.output.drain() if isinstance(m, IoPipelineHttpResponseHead)]
        assert resp.status == 101

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)

    def test_subprotocol_split_across_multiple_header_lines(self) -> None:
        # RFC 6455 §4.1 explicitly permits multiple Sec-WebSocket-Protocol header lines.
        pipeline, ibq = self._run(
            IoPipelineHttpRequestHead(
                method='GET',
                target='/ws',
                headers=_upgrade_headers(
                    ('Connection', 'Upgrade'),
                    ('Sec-Websocket-Protocol', 'superchat'),
                    ('Sec-Websocket-Protocol', 'chat, other'),
                ),
            ),
            subprotocols=('chat',),
        )

        [resp] = [m for m in pipeline.output.drain() if isinstance(m, IoPipelineHttpResponseHead)]
        assert resp.status == 101
        assert resp.headers.single['Sec-Websocket-Protocol'] == 'chat'

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)
        assert opened.subprotocol == 'chat'


class TestClientUpgradeHandler(unittest.TestCase):
    def _new(self, **kwargs):
        handler = IoPipelineWebsocketClientUpgradeHandler(host='localhost', **kwargs)
        pipeline = IoPipeline.new([
            handler,
            fbi := FeedbackInboundIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])
        return pipeline, fbi, ibq

    def test_upgrades_head_lacking_headers(self) -> None:
        pipeline, fbi, ibq = self._new()

        pipeline.feed_in(fbi.wrap(IoPipelineHttpRequestHead(
            method='GET',
            target='/',
            headers=HttpHeaders([]),
        )))

        out = pipeline.output.poll()
        assert isinstance(out, IoPipelineHttpRequestHead)
        assert out.headers.single['Upgrade'] == 'websocket'
        assert out.headers.single['Connection'] == 'Upgrade'

    def test_reuses_key_already_on_head(self) -> None:
        # Re-sending a head this handler previously returned must not desync the recorded key from the wire key.
        pipeline, fbi, ibq = self._new()

        pipeline.feed_in(fbi.wrap(IoPipelineHttpRequestHead(
            method='GET',
            target='/',
            headers=HttpHeaders([
                ('Connection', 'keep-alive'),
                ('Sec-Websocket-Key', SAMPLE_KEY),
            ]),
        )))

        out = pipeline.output.poll()
        assert isinstance(out, IoPipelineHttpRequestHead)
        assert out.headers.single['Sec-Websocket-Key'] == SAMPLE_KEY
        # A pre-existing Connection must actually be upgraded.
        assert out.headers.single['Connection'] == 'Upgrade'
        assert out.headers.single['Upgrade'] == 'websocket'

        pipeline.feed_in(IoPipelineHttpResponseHead(
            status=101,
            reason='Switching Protocols',
            headers=HttpHeaders([('Sec-Websocket-Accept', SAMPLE_ACCEPT)]),
        ))

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)

    def test_forwards_non_101_full_response_intact(self) -> None:
        pipeline, fbi, ibq = self._new()

        pipeline.feed_in(fbi.wrap(IoPipelineHttpRequestHead(
            method='GET',
            target='/',
            headers=HttpHeaders([]),
        )))
        upgraded = pipeline.output.poll()
        assert isinstance(upgraded, IoPipelineHttpRequestHead)
        key = upgraded.headers.single['Sec-Websocket-Key']

        rejected = FullIoPipelineHttpResponse(
            head=IoPipelineHttpResponseHead(
                status=403,
                reason='Forbidden',
                headers=HttpHeaders([('Content-Length', '4')]),
            ),
            body=b'nope',
        )
        pipeline.feed_in(rejected)

        [got] = ibq.drain()
        assert got is rejected

        # The rejection must not have disturbed the pending-upgrade state.
        end = IoPipelineHttpResponseEnd()
        pipeline.feed_in(
            IoPipelineHttpResponseHead(
                status=101,
                reason='Switching Protocols',
                headers=HttpHeaders([
                    ('Sec-Websocket-Accept', IoPipelineWebsocketHandshakes.compute_accept_for_key(key)),
                ]),
            ),
            end,
        )

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)

    def test_upgrades_via_full_response(self) -> None:
        pipeline, fbi, ibq = self._new()

        pipeline.feed_in(fbi.wrap(IoPipelineHttpRequestHead(
            method='GET',
            target='/',
            headers=HttpHeaders([]),
        )))
        upgraded = pipeline.output.poll()
        assert isinstance(upgraded, IoPipelineHttpRequestHead)
        key = upgraded.headers.single['Sec-Websocket-Key']

        pipeline.feed_in(FullIoPipelineHttpResponse(
            head=IoPipelineHttpResponseHead(
                status=101,
                reason='Switching Protocols',
                headers=HttpHeaders([
                    ('Sec-Websocket-Accept', IoPipelineWebsocketHandshakes.compute_accept_for_key(key)),
                ]),
            ),
            body=b'',
        ))

        [opened] = ibq.drain()
        assert isinstance(opened, IoPipelineWebsocketOpen)


class _OutboundAdapter(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)


def _encode_client_ws_text_frame(text: str) -> bytes:
    p = IoPipeline.new([
        IoPipelineWebsocketFrameEncoder(mask=True),
        _OutboundAdapter(),
    ])
    p.feed_in(IoPipelineWebsocketText(text))
    return b''.join(ByteStreamBuffers.to_bytes(part, strict=True) for part in p.output.drain())


class TestWebsocketUpgradeCoalescingAndLifecycleRegressions(unittest.TestCase):
    def test_coalesced_upgrade_request_and_ws_frame_in_single_read_and_before_defer(self) -> None:
        # Regression: IoPipelineHttpRequestDecoder decoded an HTTP Upgrade request in _HeadState -> _BodyModeState ->
        # _DoneState -> _HeadState synchronously within a single _decode() call, BEFORE the downstream
        # IoPipelineWebsocketServerUpgradeHandler ever saw the Head or its deferred handler removal ran. Any WebSocket
        # frame coalesced in the same TCP read (or arriving before the Defer ran) was swallowed into HTTP _HeadState
        # (lost on handler removal, or aborted if >4KB or containing \r\n\r\n).
        decoder = IoPipelineHttpRequestDecoder()
        encoder = IoPipelineHttpResponseEncoder()
        pipeline = IoPipeline.new([
            decoder,
            encoder,
            IoPipelineWebsocketServerUpgradeHandler(),
            IoPipelineWebsocketFrameDecoder(expect_masked=True),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        upgrade_req = (
            b'GET /ws HTTP/1.1\r\n'
            b'Host: localhost\r\n'
            b'Upgrade: websocket\r\n'
            b'Connection: Upgrade\r\n'
            b'Sec-Websocket-Version: 13\r\n'
            b'Sec-Websocket-Key: ' + SAMPLE_KEY.encode('ascii') + b'\r\n'
            b'\r\n'
        )
        # Deliberately >4KB and contains \r\n\r\n so _HeadState would abort/corrupt it if treated as HTTP.
        payload1 = 'first-coalesced\r\n\r\n' + ('x' * 5000)
        frame1 = _encode_client_ws_text_frame(payload1)
        frame2 = _encode_client_ws_text_frame('second-before-defer')
        frame3 = _encode_client_ws_text_frame('third-after-defer')

        # 1. Feed upgrade request + frame1 together in one TCP read; do NOT run deferred handler removal yet.
        pipeline.feed_in(upgrade_req + frame1)

        out = pipeline.output.drain()
        wire_resp = b''.join(ByteStreamBuffers.to_bytes(m, strict=True) for m in out if ByteStreamBuffers.can_bytes(m))
        defers = [m for m in out if isinstance(m, IoPipelineMessages.Defer)]
        self.assertIn(b'HTTP/1.1 101 Switching Protocols\r\n', wire_resp)
        self.assertIn(f'Sec-Websocket-Accept: {SAMPLE_ACCEPT}\r\n'.encode('ascii'), wire_resp)
        self.assertEqual(len(defers), 1)

        opened, got1 = ibq.drain()
        self.assertIsInstance(opened, IoPipelineWebsocketOpen)
        self.assertIsInstance(got1, IoPipelineWebsocketFrame)
        self.assertEqual(got1.opcode, IoPipelineWebsocketOpcode.TEXT)
        self.assertEqual(ByteStreamBuffers.to_bytes(got1.payload, strict=True), payload1.encode('utf-8'))

        # 2. Feed frame2 BEFORE running the deferred removal - decoder is already in tunnel mode, so it passes through.
        pipeline.feed_in(frame2)
        [got2] = ibq.drain()
        self.assertIsInstance(got2, IoPipelineWebsocketFrame)
        self.assertEqual(ByteStreamBuffers.to_bytes(got2.payload, strict=True), b'second-before-defer')

        # 3. Run deferred removal, verify HTTP handlers are removed, and feed frame3.
        pipeline.run_deferred(defers[0])
        self.assertIsNone(pipeline.find_handler(decoder))
        self.assertIsNone(pipeline.find_handler(encoder))

        pipeline.feed_in(frame3)
        [got3] = ibq.drain()
        self.assertIsInstance(got3, IoPipelineWebsocketFrame)
        self.assertEqual(ByteStreamBuffers.to_bytes(got3.payload, strict=True), b'third-after-defer')

    def test_rejected_upgrade_resumes_http_decoding_on_pipelined_request(self) -> None:
        # When an Upgrade request is rejected with a non-101 response (e.g. 403) on a keep-alive connection,
        # IoPipelineHttpRequestDecoder must leave _PendingUpgradeState and parse any parked bytes as the next HTTP
        # request.
        class _RejectUpgradeHandler(IoPipelineHandler):
            def __init__(self) -> None:
                super().__init__()
                self.heads: ta.List[IoPipelineHttpRequestHead] = []

            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if isinstance(msg, IoPipelineHttpRequestHead):
                    self.heads.append(msg)
                    if msg.target == '/ws':
                        ctx.feed_out(FullIoPipelineHttpResponse(
                            head=IoPipelineHttpResponseHead(
                                status=403,
                                reason='Forbidden',
                                headers=HttpHeaders([('Content-Length', '4')]),
                            ),
                            body=b'nope',
                        ))
                    return
                ctx.feed_in(msg)

        app = _RejectUpgradeHandler()
        pipeline = IoPipeline.new(
            [
                IoPipelineHttpResponseEncoder(),
                IoPipelineHttpRequestDecoder(),
                app,
            ],
            IoPipeline.Config(inbound_terminal='drop'),
        )

        pipeline.feed_in(
            b'GET /ws HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n'
            b'GET /after HTTP/1.1\r\nHost: localhost\r\n\r\n',
        )

        self.assertEqual([h.target for h in app.heads], ['/ws', '/after'])

    def test_upgrade_defer_does_not_create_ref_cycle(self) -> None:
        # Regression: server and client upgrade handlers previously deferred `lambda: self._remove_http_handlers(ctx)`,
        # capturing ctx in the Defer stored in pipeline.output and creating a pipeline -> Defer -> ctx -> pipeline
        # reference cycle.
        def make_server_ref() -> weakref.ReferenceType:
            pipeline = IoPipeline.new([
                IoPipelineHttpRequestDecoder(),
                IoPipelineHttpResponseEncoder(),
                IoPipelineWebsocketServerUpgradeHandler(),
                InboundQueueIoPipelineHandler(),
            ])
            pipeline.feed_in(
                b'GET /ws HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                b'Sec-Websocket-Version: 13\r\nSec-Websocket-Key: ' + SAMPLE_KEY.encode('ascii') + b'\r\n\r\n',
            )
            return weakref.ref(pipeline)

        def make_client_ref() -> weakref.ReferenceType:
            fbi = FeedbackInboundIoPipelineHandler()
            pipeline = IoPipeline.new([
                IoPipelineWebsocketClientUpgradeHandler(host='localhost'),
                fbi,
                InboundQueueIoPipelineHandler(),
            ])
            pipeline.feed_in(fbi.wrap(IoPipelineHttpRequestHead(
                method='GET',
                target='/ws',
                headers=HttpHeaders([('Sec-Websocket-Key', SAMPLE_KEY)]),
            )))
            pipeline.output.drain()
            pipeline.feed_in(IoPipelineHttpResponseHead(
                status=101,
                reason='Switching Protocols',
                headers=HttpHeaders([('Sec-Websocket-Accept', SAMPLE_ACCEPT)]),
            ))
            return weakref.ref(pipeline)

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            self.assertIsNone(make_server_ref()())
            self.assertIsNone(make_client_ref()())
        finally:
            if was_enabled:
                gc.enable()
