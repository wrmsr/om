# ruff: noqa: UP006 UP007 UP045
# @om-lite
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....headers import HttpHeaders
from ...requests import FullIoPipelineHttpRequest
from ...requests import IoPipelineHttpRequestHead
from ...responses import FullIoPipelineHttpResponse
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..handshakes import IoPipelineWebsocketClientUpgradeHandler
from ..handshakes import IoPipelineWebsocketHandshakes
from ..handshakes import IoPipelineWebsocketServerUpgradeHandler
from ..objects import IoPipelineWebsocketOpen


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
