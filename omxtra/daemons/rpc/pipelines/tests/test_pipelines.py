import contextlib
import typing as ta
import uuid

import pytest

from omcore.io.pipelines.drivers.pure.drivers import PureIoPipelineDriver
from omcore.rpc.connection import RpcConnection
from omcore.rpc.connection import SyncRpcConnection
from omcore.rpc.errors import RpcMessageTooLargeError
from omcore.rpc.handshake import RpcHandshakeCompletedEvent
from omcore.rpc.messages import RpcErrorMessage
from omcore.rpc.messages import RpcResultMessage
from omcore.rpc.messages import RpcSessionMessages
from omcore.rpc.pure import PureRpcLink

from ...connections import RpcClientRpcConnection
from ...connections import RpcServerHandler
from ...protocol import RPC_PROTOCOL_NAME
from ...protocol import RPC_PROTOCOL_VERSION
from ...protocol import RpcCallIndeterminateError
from ...protocol import RpcProtocolError
from ...protocol import RpcRemoteError
from ...protocol import RpcRequest
from ...protocol import RpcUnavailableError
from ...protocol import encode_rpc_message
from ...protocol import error_message
from ...protocol import hello_message
from ...protocol import request_message
from ...protocol import result_message
from .. import RpcWireError
from .. import RpcWireResponse
from .. import RpcWireResult
from .. import rpc_client_pipeline
from .. import rpc_request_id
from .. import rpc_server_pipeline


##


class _Pair(ta.NamedTuple):
    link: PureRpcLink
    instance_id: uuid.UUID
    client: RpcClientRpcConnection
    client_sync: SyncRpcConnection
    server: RpcConnection
    server_sync: SyncRpcConnection
    dispatched: list[RpcRequest]


def _echo_response(request: RpcRequest) -> RpcWireResponse:
    return RpcWireResult(
        client_id=request.client_id,
        request_id=request.request_id,
        result={'method': request.method, 'params': request.params},
    )


def _new_pair(
        *,
        respond: ta.Callable[[RpcRequest], RpcWireResponse] = _echo_response,
        acquire_activity: ta.Callable[[], ta.ContextManager[ta.Any] | None] = contextlib.nullcontext,
        client_version: int = RPC_PROTOCOL_VERSION,
        client_max_frame_bytes: int = 1_024,
        server_max_frame_bytes: int = 1_024,
        io_timeout_s: float | None = 30.,
        connection_timeout_s: float | None = 30.,
        capacity: int | None = None,
) -> _Pair:
    instance_id = uuid.uuid7()
    cp = rpc_client_pipeline(
        protocol_version=client_version,
        max_frame_bytes=client_max_frame_bytes,
        io_timeout_s=io_timeout_s,
    )
    sp = rpc_server_pipeline(
        protocol_version=RPC_PROTOCOL_VERSION,
        instance_id=instance_id,
        max_frame_bytes=server_max_frame_bytes,
        connection_timeout_s=connection_timeout_s,
    )
    link = PureRpcLink(cp.spec, sp.spec, capacity=capacity)

    dispatched: list[RpcRequest] = []

    async def dispatch(request: RpcRequest) -> RpcWireResponse:
        dispatched.append(request)
        return respond(request)

    client = RpcClientRpcConnection(
        link.a,
        cp.config,
        max_frame_bytes=client_max_frame_bytes,
        io_timeout_s=io_timeout_s,
    )
    handler = RpcServerHandler(dispatch, acquire_activity)
    server = RpcConnection(link.b, sp.config, handler=handler)
    server.add_close_callback(handler.release_activity)

    client_sync = SyncRpcConnection(client)
    server_sync = SyncRpcConnection(server)
    client_sync.start()
    server_sync.start()

    return _Pair(link, instance_id, client, client_sync, server, server_sync, dispatched)


def _request(method: str = 'echo', params: ta.Any = None) -> RpcRequest:
    return RpcRequest(
        client_id='client',
        request_id='request',
        method=method,
        params=params,
    )


##


def test_fragmented_conversation_closes_after_the_answer():
    p = _new_pair(capacity=1)
    assert p.client_sync.run(p.client.handshake()) == p.instance_id

    request = _request(params={'value': 42})
    p.client_sync.run(p.client.send_rpc(request))
    assert p.client_sync.run(p.client.receive_rpc()) == {'method': 'echo', 'params': {'value': 42}}
    assert p.dispatched == [request]

    # The server closes behind its one answer, and the client hears it end.
    p.server_sync.wait_closed()
    assert p.server.close_exception is None
    p.client_sync.wait_closed()
    assert p.client.close_exception is None


@pytest.mark.parametrize(('response', 'exc_type'), [
    (RpcWireError(client_id='client', request_id='request', code='remote', remote_type='builtins.RuntimeError', message='boom'), RpcRemoteError),  # noqa
    (RpcWireError(client_id='client', request_id='request', code='unavailable', remote_type='x.Busy', message='busy'), RpcUnavailableError),  # noqa
    (RpcWireError(client_id='client', request_id='request', code='protocol', remote_type='x.Bad', message='bad'), RpcProtocolError),  # noqa
    (RpcWireError(client_id='client', request_id='request', code='weird', remote_type='x.Weird', message='?'), RpcCallIndeterminateError),  # noqa
])
def test_error_responses_classify_by_code(response: RpcWireError, exc_type: type):
    p = _new_pair(respond=lambda _: response)
    p.client_sync.run(p.client.handshake())

    request = _request()
    p.client_sync.run(p.client.send_rpc(request))
    with pytest.raises(exc_type) as ei:
        p.client_sync.run(p.client.receive_rpc())

    if isinstance(ei.value, RpcRemoteError):
        assert ei.value.remote_type == 'builtins.RuntimeError'
        assert ei.value.message == 'boom'
    elif isinstance(ei.value, RpcCallIndeterminateError):
        assert ei.value.instance_id == p.instance_id
    else:
        assert str(ei.value) == response.message


def test_shutting_down_server_refuses_unrun():
    p = _new_pair(acquire_activity=lambda: None)
    p.client_sync.run(p.client.handshake())
    p.client_sync.run(p.client.send_rpc(_request()))
    with pytest.raises(RpcUnavailableError):
        p.client_sync.run(p.client.receive_rpc())
    assert p.dispatched == []


def test_activity_is_held_until_the_connection_closes():
    events: list[str] = []

    @contextlib.contextmanager
    def activity():
        events.append('enter')
        yield
        events.append('exit')

    def respond(request: RpcRequest) -> RpcWireResponse:
        events.append('dispatch')
        return _echo_response(request)

    p = _new_pair(respond=respond, acquire_activity=activity)
    p.client_sync.run(p.client.handshake())
    p.client_sync.run(p.client.send_rpc(_request()))
    p.client_sync.run(p.client.receive_rpc())
    p.server_sync.wait_closed()
    assert events == ['enter', 'dispatch', 'exit']


def test_oversized_inbound_frame_fails_the_connection():
    # The client's greeting alone exceeds what the server accepts.
    p = _new_pair(server_max_frame_bytes=8)
    with pytest.raises(RpcUnavailableError):
        p.client_sync.run(p.client.handshake())

    p.server_sync.wait_closed()
    assert isinstance(p.server.close_exception, RpcMessageTooLargeError)


def test_version_mismatch_greets_then_refuses():
    p = _new_pair(client_version=RPC_PROTOCOL_VERSION + 1)
    with pytest.raises(RpcProtocolError, match='version mismatch'):
        p.client_sync.run(p.client.handshake())

    p.server_sync.wait_closed()
    assert p.server.close_exception is not None


def test_unsendable_requests_are_refused_unsent():
    p = _new_pair(client_max_frame_bytes=256)
    p.client_sync.run(p.client.handshake())

    with pytest.raises(RpcProtocolError, match='not JSON-compatible'):
        p.client_sync.run(p.client.send_rpc(_request(params=object())))
    with pytest.raises(RpcProtocolError, match='not JSON-compatible'):
        p.client_sync.run(p.client.send_rpc(_request(params=float('nan'))))
    with pytest.raises(RpcProtocolError, match='exceeding limit 256'):
        p.client_sync.run(p.client.send_rpc(_request(params='x' * 300)))

    # Nothing was sent, so the connection is still good for its one request.
    p.client_sync.run(p.client.send_rpc(_request(params=1)))
    assert p.client_sync.run(p.client.receive_rpc()) == {'method': 'echo', 'params': 1}
    assert len(p.dispatched) == 1


def test_silent_client_is_closed_after_the_connection_timeout():
    p = _new_pair(connection_timeout_s=5.)
    p.client_sync.run(p.client.handshake())

    p.server_sync.wait_closed()
    assert p.link.now >= 5.
    assert p.dispatched == []


##
# bytes


def _frame(obj: ta.Mapping[str, ta.Any]) -> bytes:
    return encode_rpc_message(obj, 1_024)


def test_bytes_match_the_blocking_wire_helpers():
    instance_id = uuid.uuid7()
    client = PureIoPipelineDriver(rpc_client_pipeline(
        protocol_version=RPC_PROTOCOL_VERSION,
        max_frame_bytes=1_024,
    ).spec)
    server = PureIoPipelineDriver(rpc_server_pipeline(
        protocol_version=RPC_PROTOCOL_VERSION,
        instance_id=instance_id,
        max_frame_bytes=1_024,
    ).spec)

    assert client.next(read=False) is None
    assert client.drain_output() == _frame(hello_message(version=RPC_PROTOCOL_VERSION))

    for b in _frame(hello_message(version=RPC_PROTOCOL_VERSION)):
        server.feed_input(bytes([b]))
    completed = server.next()
    assert isinstance(completed, RpcHandshakeCompletedEvent)
    assert completed.peer_hello == {'protocol': RPC_PROTOCOL_NAME, 'version': RPC_PROTOCOL_VERSION}
    assert server.next(read=False) is None
    assert server.drain_output() == _frame(hello_message(version=RPC_PROTOCOL_VERSION, instance_id=instance_id))

    request = _request(params={'value': 'ü'})
    server.feed_input(_frame(request_message(request)))
    received = server.next()
    assert isinstance(received, RpcSessionMessages.RequestReceived)
    assert received.request.id == rpc_request_id('client', 'request')
    assert received.request.params == {'value': 'ü'}

    server.enqueue(RpcSessionMessages.SendResponse(RpcResultMessage(received.request.id, {'ok': 'ü'})))
    while server.next(read=False) is not None:
        pass
    assert server.drain_output().startswith(_frame(result_message(request, {'ok': 'ü'})))


def test_error_bytes_match_the_blocking_wire_helpers():
    from omcore.rpc.errors import RpcRemoteErrorData

    from .. import DAEMONS_RPC_ENVELOPE_CODEC

    request = _request()
    envelope = RpcErrorMessage(rpc_request_id('client', 'request'), RpcRemoteErrorData(
        code='remote',
        remote_type='builtins.RuntimeError',
        message='boom',
    ))
    assert DAEMONS_RPC_ENVELOPE_CODEC.encode(envelope) == _frame(error_message(
        request,
        code='remote',
        remote_type='builtins.RuntimeError',
        message='boom',
    ))[4:]


@pytest.mark.parametrize(('payload', 'match'), [
    (b'not json', 'Invalid RPC JSON'),
    (b'[]', 'must be an object'),
    (b'{"type":"nope","client_id":"c","request_id":"r"}', 'Unknown RPC message type'),
    (b'{"type":"result","client_id":"c","request_id":"r"}', 'Missing RPC result'),
    (b'{"type":"request","client_id":"","request_id":"r","method":"m"}', "Invalid RPC message field 'client_id'"),
    (b'{"type":"error","client_id":"c","request_id":"r","error":{"code":"x","type":"y"}}', "Missing RPC message field: 'message'"),  # noqa
])
def test_malformed_messages_are_protocol_errors(payload: bytes, match: str):
    from .. import DAEMONS_RPC_ENVELOPE_CODEC

    with pytest.raises(RpcProtocolError, match=match):
        DAEMONS_RPC_ENVELOPE_CODEC.decode(payload)
