# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import logging
import typing as ta
import unittest

from ...lite.asyncs import sync_await
from ..closing import RpcCloseAfterRequestsIoPipelineHandler
from ..codecs import RpcValueEnvelopeCodec
from ..configs import RpcConfig
from ..connection import RpcConnection
from ..connection import SyncRpcConnection
from ..dispatch import RpcHandler
from ..dispatch import RpcMethodTableHandler
from ..dispatch import rpc_async_method
from ..errors import RpcConnectionClosedError
from ..errors import RpcHandlerError
from ..errors import RpcProtocolError
from ..errors import RpcRemoteError
from ..errors import RpcRemoteErrorData
from ..handshake import RpcHandshakeCompletedEvent
from ..handshake import RpcHandshakeIoPipelineHandler
from ..messages import RpcHelloMessage
from ..messages import RpcRequestMessage
from ..messages import RpcResultMessage
from ..messages import RpcSessionMessages
from ..pure import PureRpcLink
from ..specs import rpc_build_pipeline_spec
from .raw import RawRpcPeer


##


class _HandshakeRecordingRpcConnection(RpcConnection):
    def __init__(self, *args: ta.Any, **kwargs: ta.Any) -> None:
        super().__init__(*args, **kwargs)

        self.handshakes: ta.List[ta.Mapping[str, ta.Any]] = []

    async def _on_other_event(self, event: ta.Any) -> None:
        if isinstance(event, RpcHandshakeCompletedEvent):
            self.handshakes.append(event.peer_hello)
            return
        await super()._on_other_event(event)


def _check_version(hello: ta.Mapping[str, ta.Any]) -> None:
    if hello.get('version') != 1:
        raise RpcProtocolError(f'bad version: {hello.get("version")!r}')


class _HandshakePair:
    def __init__(
            self,
            client_hello: ta.Mapping[str, ta.Any],
            server_hello: ta.Mapping[str, ta.Any],
            *,
            server_handler: ta.Optional[RpcHandler] = None,
            server_between: ta.Sequence[ta.Any] = (),
    ) -> None:
        self.ch = RpcHandshakeIoPipelineHandler(client_hello, initiate=True, validate=_check_version)
        self.sh = RpcHandshakeIoPipelineHandler(server_hello, initiate=False, validate=_check_version)
        self.link = PureRpcLink(
            rpc_build_pipeline_spec(handshake_handler=self.ch),
            rpc_build_pipeline_spec(handshake_handler=self.sh, between_handlers=server_between),
        )
        self.client = _HandshakeRecordingRpcConnection(self.link.a)
        self.server = _HandshakeRecordingRpcConnection(self.link.b, handler=server_handler)
        self.c = SyncRpcConnection(self.client)
        self.s = SyncRpcConnection(self.server)
        self.c.start()
        self.s.start()


class TestHello(unittest.TestCase):
    def test_codec(self):
        c = RpcValueEnvelopeCodec()
        env = RpcHelloMessage({'protocol': 'x', 'version': 2})
        self.assertEqual(c.envelope_to_value(env), {'type': 'hello', 'protocol': 'x', 'version': 2})
        self.assertEqual(c.decode(c.encode(env)), env)
        with self.assertRaises(ValueError):
            c.encode(RpcHelloMessage({'type': 'nope'}))
        with self.assertRaises(RpcProtocolError):
            RpcHelloMessage({1: 2})  # type: ignore[dict-item]


class TestHandshake(unittest.TestCase):
    def test_handshake_then_requests(self):
        p = _HandshakePair(
            {'version': 1, 'who': 'client'},
            {'version': 1, 'who': 'server', 'instance': 'abc'},
            server_handler=RpcMethodTableHandler({'echo': rpc_async_method(lambda x: x)}),
        )

        # Made before any greeting has crossed: held, then sent once the handshake completes.
        self.assertEqual(p.c.request('echo', 'hi'), 'hi')

        self.assertTrue(p.ch.completed)
        self.assertTrue(p.sh.completed)
        self.assertEqual(p.client.handshakes, [{'version': 1, 'who': 'server', 'instance': 'abc'}])
        self.assertEqual(p.server.handshakes, [{'version': 1, 'who': 'client'}])
        self.assertEqual(p.ch.peer_hello, {'version': 1, 'who': 'server', 'instance': 'abc'})

        p.c.ping()
        p.c.close()
        p.s.wait_closed()

    def test_unconsumed_completion_is_quiet(self):
        # Plain connections, which do not consume the completion event: it passes by without a warning.
        ch = RpcHandshakeIoPipelineHandler({'version': 1}, initiate=True)
        sh = RpcHandshakeIoPipelineHandler({'version': 1}, initiate=False)
        link = PureRpcLink(
            rpc_build_pipeline_spec(handshake_handler=ch),
            rpc_build_pipeline_spec(handshake_handler=sh),
        )
        c = SyncRpcConnection(RpcConnection(link.a))
        s = SyncRpcConnection(RpcConnection(link.b, handler=RpcMethodTableHandler({'echo': rpc_async_method(lambda x: x)})))  # noqa

        records: ta.List[logging.LogRecord] = []

        class _Capture(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                records.append(record)

        rpc_log = logging.getLogger(RpcConnection.__module__)
        capture = _Capture(logging.WARNING)
        rpc_log.addHandler(capture)
        try:
            c.start()
            s.start()
            self.assertEqual(c.request('echo', 'hi'), 'hi')
            c.close()
            s.wait_closed()
        finally:
            rpc_log.removeHandler(capture)

        self.assertEqual(records, [])

    def test_refused_by_server(self):
        p = _HandshakePair({'version': 2}, {'version': 1, 'instance': 'abc'})
        with self.assertRaises(RpcConnectionClosedError):
            p.c.request('echo', 'hi')
        # The server greeted back before refusing, so the client learned who it reached.
        self.assertEqual(p.ch.peer_hello, {'version': 1, 'instance': 'abc'})
        p.s.wait_closed()
        self.assertIsInstance(p.server.close_exception, RpcProtocolError)

    def test_refused_by_client(self):
        p = _HandshakePair({'version': 1}, {'version': 3})
        with self.assertRaises(RpcConnectionClosedError):
            p.c.request('echo', 'hi')
        p.c.wait_closed()
        self.assertIsInstance(p.client.close_exception, RpcProtocolError)
        self.assertFalse(p.ch.completed)

    def test_envelope_before_hello_is_fatal(self):
        hs = RpcHandshakeIoPipelineHandler({'version': 1}, initiate=False)
        p = RawRpcPeer(handshake_handler=hs)
        p.send(RpcRequestMessage(1, 'm'))
        [closed] = p.take_events(RpcSessionMessages.Closed)
        self.assertIsInstance(closed.exc, RpcProtocolError)

    def test_second_hello_is_fatal(self):
        hs = RpcHandshakeIoPipelineHandler({'version': 1}, initiate=False)
        p = RawRpcPeer(handshake_handler=hs)
        p.send(RpcHelloMessage({'version': 1}))
        self.assertEqual(p.recv(), [RpcHelloMessage({'version': 1})])
        [ev] = p.take_events()
        self.assertIsInstance(ev, RpcHandshakeCompletedEvent)
        p.send(RpcHelloMessage({'version': 1}))
        [closed] = p.take_events(RpcSessionMessages.Closed)
        self.assertIsInstance(closed.exc, RpcProtocolError)


class TestCloseAfterRequests(unittest.TestCase):
    def test_one_request_per_connection(self):
        p = RawRpcPeer(between_handlers=[RpcCloseAfterRequestsIoPipelineHandler()])
        p.send(RpcRequestMessage(1, 'm'))
        p.take_events()
        p.cmd(RpcSessionMessages.SendResponse(RpcResultMessage(1, 'ok')))
        self.assertEqual(p.recv(), [RpcResultMessage(1, 'ok')])
        self.assertEqual(p.take_events(RpcSessionMessages.Closed), [RpcSessionMessages.Closed(None)])
        self.assertFalse(p.is_live)

    def test_second_request_is_fatal(self):
        p = RawRpcPeer(between_handlers=[RpcCloseAfterRequestsIoPipelineHandler()])
        p.send(RpcRequestMessage(1, 'm'), RpcRequestMessage(2, 'm'))
        [closed] = p.take_events(RpcSessionMessages.Closed)
        self.assertIsInstance(closed.exc, RpcProtocolError)

    def test_over_a_connection(self):
        p = _HandshakePair(
            {'version': 1},
            {'version': 1},
            server_handler=RpcMethodTableHandler({'echo': rpc_async_method(lambda x: x)}),
            server_between=[RpcCloseAfterRequestsIoPipelineHandler()],
        )
        self.assertEqual(p.c.request('echo', 1), 1)
        p.s.wait_closed()
        p.c.wait_closed()
        self.assertIsNone(p.server.close_exception)


class TestHandlerAnswers(unittest.TestCase):
    def test_handler_error_answers_verbatim(self):
        data = RpcRemoteErrorData('unavailable', 'x.Draining', 'shutting down')

        def refuse(p: ta.Any) -> ta.Any:
            raise RpcHandlerError(data)

        link = PureRpcLink.of_configs(RpcConfig())
        a = SyncRpcConnection(RpcConnection(link.a))
        b = SyncRpcConnection(RpcConnection(link.b, handler=RpcMethodTableHandler({'r': rpc_async_method(refuse)})))
        a.start()
        b.start()
        with self.assertRaises(RpcRemoteError) as cm:
            a.request('r')
        self.assertEqual(cm.exception.data, data)

    def test_request_message_hook(self):
        seen: ta.List[RpcRequestMessage] = []

        class H(RpcHandler):
            async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
                raise NotImplementedError

            async def handle_request_message(self, request: RpcRequestMessage) -> ta.Any:
                seen.append(request)
                return request.id

        link = PureRpcLink.of_configs()
        a = RpcConnection(link.a, id_creator=lambda: 'fixed-id')
        b = RpcConnection(link.b, handler=H())
        sync_await(a.start())
        sync_await(b.start())
        self.assertEqual(sync_await(a.request('m', 1)), 'fixed-id')
        self.assertEqual(seen, [RpcRequestMessage('fixed-id', 'm', 1)])
