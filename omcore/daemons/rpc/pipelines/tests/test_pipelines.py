import uuid

from .....io.pipelines.drivers.pure import PureIoPipelineDriver
from ...protocol import RPC_PROTOCOL_VERSION
from ...protocol import RpcProtocolError
from ...protocol import RpcRequest
from .. import RpcClientConnected
from .. import RpcClientRequestSent
from .. import RpcClientResponse
from .. import RpcClientSendRequest
from .. import RpcPipelineFailure
from .. import RpcServerDispatch
from .. import RpcServerSendResponse
from .. import RpcWireError
from .. import RpcWireResult
from .. import rpc_client_pipeline_spec
from .. import rpc_server_pipeline_spec


##


def _drive_initial_output(driver: PureIoPipelineDriver) -> bytes:
    assert driver.next(read=False) is None
    return driver.drain_output()


def _feed_fragmented(driver: PureIoPipelineDriver, data: bytes) -> None:
    for byte in data:
        driver.feed_input(bytes([byte]))


def _new_pair(
        *,
        max_frame_bytes: int = 1_024,
) -> tuple[PureIoPipelineDriver, PureIoPipelineDriver, uuid.UUID]:
    instance_id = uuid.uuid7()
    return (
        PureIoPipelineDriver(rpc_client_pipeline_spec(
            protocol_version=RPC_PROTOCOL_VERSION,
            max_frame_bytes=max_frame_bytes,
        )),
        PureIoPipelineDriver(rpc_server_pipeline_spec(
            protocol_version=RPC_PROTOCOL_VERSION,
            instance_id=instance_id,
            max_frame_bytes=max_frame_bytes,
        )),
        instance_id,
    )


def _handshake(
        client: PureIoPipelineDriver,
        server: PureIoPipelineDriver,
) -> RpcClientConnected:
    _feed_fragmented(server, _drive_initial_output(client))
    assert server.next() is None

    _feed_fragmented(client, server.drain_output())
    connected = client.next()
    assert isinstance(connected, RpcClientConnected)
    return connected


##


def test_rpc_pipeline_pure_driver_fragmented_conversation():
    client, server, instance_id = _new_pair()
    assert _handshake(client, server).instance_id == instance_id

    request = RpcRequest(
        client_id='client',
        request_id='request',
        method='echo',
        params={'value': 42},
    )
    client.enqueue(RpcClientSendRequest(request=request))
    request_bytes = _drive_initial_output(client)
    assert client.next(read=False) == RpcClientRequestSent(request=request)
    _feed_fragmented(server, request_bytes)

    dispatch = server.next()
    assert dispatch == RpcServerDispatch(request=request)

    server.enqueue(RpcServerSendResponse(response=RpcWireResult(
        client_id=request.client_id,
        request_id=request.request_id,
        result={'value': 42},
    )))
    assert server.next(read=False) is None
    response_bytes = server.drain_output()
    assert not server.is_running

    _feed_fragmented(client, response_bytes)
    response = client.next()
    assert response == RpcClientResponse(response=RpcWireResult(
        client_id=request.client_id,
        request_id=request.request_id,
        result={'value': 42},
    ))
    assert client.next(read=False) is None
    assert client.drain_output() == b''
    assert not client.is_running


def test_rpc_pipeline_pure_driver_error_response():
    client, server, _ = _new_pair()
    _handshake(client, server)

    request = RpcRequest(
        client_id='client',
        request_id='request',
        method='fail',
    )
    client.enqueue(RpcClientSendRequest(request=request))
    request_bytes = _drive_initial_output(client)
    assert client.next(read=False) == RpcClientRequestSent(request=request)
    server.feed_input(request_bytes)
    assert server.next() == RpcServerDispatch(request=request)

    wire_error = RpcWireError(
        client_id=request.client_id,
        request_id=request.request_id,
        code='remote',
        remote_type='builtins.RuntimeError',
        message='boom',
    )
    server.enqueue(RpcServerSendResponse(response=wire_error))
    assert server.next(read=False) is None
    client.feed_input(server.drain_output())
    assert client.next() == RpcClientResponse(response=wire_error)


def test_rpc_pipeline_rejects_oversized_inbound_frame_before_payload():
    _, server, _ = _new_pair(max_frame_bytes=8)
    server.feed_input((9).to_bytes(4, 'big'))

    error = server.next()
    assert isinstance(error, RpcPipelineFailure)
    assert isinstance(error.exc, RpcProtocolError)
    assert 'exceeding limit 8' in str(error.exc)
    assert server.next(read=False) is None
    assert server.drain_output() == b''
    assert not server.is_running


def test_rpc_pipeline_rejects_truncated_frame_at_eof():
    _, server, _ = _new_pair()
    server.feed_input((12).to_bytes(4, 'big') + b'{}')
    server.feed_eof()

    error = server.next()
    assert isinstance(error, RpcPipelineFailure)
    assert isinstance(error.exc, RpcProtocolError)
    assert str(error.exc) == 'RPC connection closed within a frame'


def test_rpc_pipeline_rejects_invalid_json_without_a_socket():
    _, server, _ = _new_pair()
    payload = b'not json'
    server.feed_input(len(payload).to_bytes(4, 'big') + payload)

    error = server.next()
    assert isinstance(error, RpcPipelineFailure)
    assert isinstance(error.exc, RpcProtocolError)
    assert 'Invalid RPC JSON' in str(error.exc)


def test_rpc_pipeline_version_mismatch_returns_hello_then_closes():
    instance_id = uuid.uuid7()
    client = PureIoPipelineDriver(rpc_client_pipeline_spec(
        protocol_version=RPC_PROTOCOL_VERSION + 1,
        max_frame_bytes=1_024,
    ))
    server = PureIoPipelineDriver(rpc_server_pipeline_spec(
        protocol_version=RPC_PROTOCOL_VERSION,
        instance_id=instance_id,
        max_frame_bytes=1_024,
    ))

    server.feed_input(_drive_initial_output(client))
    assert server.next() is None
    client.feed_input(server.drain_output())

    error = client.next()
    assert isinstance(error, RpcPipelineFailure)
    assert isinstance(error.exc, RpcProtocolError)
    assert 'version mismatch' in str(error.exc)


def test_rpc_pipeline_non_json_request_fails_without_reentrant_final_output():
    client, server, _ = _new_pair()
    _handshake(client, server)

    request = RpcRequest(
        client_id='client',
        request_id='request',
        method='invalid',
        params=object(),
    )
    client.enqueue(RpcClientSendRequest(request=request))
    failure = client.next(read=False)
    assert isinstance(failure, RpcPipelineFailure)
    assert isinstance(failure.exc, RpcProtocolError)
    assert 'not JSON-compatible' in str(failure.exc)
    assert client.next(read=False) is None
    assert client.drain_output() == b''
    assert not client.is_running
