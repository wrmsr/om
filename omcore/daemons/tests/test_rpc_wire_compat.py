import os
import socket
import tempfile
import threading
import time
import typing as ta
import uuid

from ..rpc import RpcClient
from ..rpc import RpcRequest
from ..rpc import RpcServer
from ..rpc import RpcServerConfig
from ..rpc import SimpleRpcServerRuntime
from ..rpc.protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from ..rpc.protocol import RPC_PROTOCOL_VERSION
from ..rpc.protocol import hello_message
from ..rpc.protocol import recv_rpc_message
from ..rpc.protocol import request_message
from ..rpc.protocol import result_message
from ..rpc.protocol import send_rpc_message
from .testing import TEST_TIMEOUT_S


##


def _wait_path(path: str) -> None:
    deadline = time.monotonic() + TEST_TIMEOUT_S
    while not os.path.exists(path):
        if time.monotonic() >= deadline:
            raise TimeoutError(f'Path was not created: {path!r}')
        time.sleep(.01)


def test_blocking_wire_helpers_interoperate_with_pipeline_server():
    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, 'rpc.sock')

        def handler(request: RpcRequest) -> ta.Any:
            return {'method': request.method, 'params': request.params}

        runtime = SimpleRpcServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
        server = RpcServer(RpcServerConfig(
            socket_path=socket_path,
            handler=handler,
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        errors: list[BaseException] = []

        def serve() -> None:
            try:
                server.run(runtime)
            except BaseException as exc:  # noqa
                errors.append(exc)

        thread = threading.Thread(target=serve)
        thread.start()
        try:
            _wait_path(socket_path)
            request = RpcRequest(
                client_id='legacy-client',
                request_id='legacy-request',
                method='echo',
                params={'wire': 'legacy'},
            )
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.settimeout(TEST_TIMEOUT_S)
                sock.connect(socket_path)
                send_rpc_message(
                    sock,
                    hello_message(version=RPC_PROTOCOL_VERSION),
                    RPC_DEFAULT_MAX_FRAME_BYTES,
                )
                hello = recv_rpc_message(sock, RPC_DEFAULT_MAX_FRAME_BYTES)
                assert hello['type'] == 'hello'
                assert hello['version'] == RPC_PROTOCOL_VERSION
                assert isinstance(uuid.UUID(hello['instance_id']), uuid.UUID)

                send_rpc_message(
                    sock,
                    request_message(request),
                    RPC_DEFAULT_MAX_FRAME_BYTES,
                )
                assert recv_rpc_message(sock, RPC_DEFAULT_MAX_FRAME_BYTES) == {
                    'type': 'result',
                    'client_id': request.client_id,
                    'request_id': request.request_id,
                    'result': {'method': 'echo', 'params': {'wire': 'legacy'}},
                }
        finally:
            runtime.request_shutdown()
            thread.join(TEST_TIMEOUT_S)

        assert not thread.is_alive()
        assert not errors


def test_pipeline_client_interoperates_with_blocking_wire_helpers():
    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, 'rpc.sock')
        instance_id = uuid.uuid7()
        errors: list[BaseException] = []

        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(socket_path)
        listener.listen()

        def serve() -> None:
            try:
                conn, _ = listener.accept()
                with conn:
                    conn.settimeout(TEST_TIMEOUT_S)
                    hello = recv_rpc_message(conn, RPC_DEFAULT_MAX_FRAME_BYTES)
                    assert hello == hello_message(version=RPC_PROTOCOL_VERSION)
                    send_rpc_message(
                        conn,
                        hello_message(
                            version=RPC_PROTOCOL_VERSION,
                            instance_id=instance_id,
                        ),
                        RPC_DEFAULT_MAX_FRAME_BYTES,
                    )

                    request_obj = recv_rpc_message(conn, RPC_DEFAULT_MAX_FRAME_BYTES)
                    request = RpcRequest(
                        client_id=request_obj['client_id'],
                        request_id=request_obj['request_id'],
                        method=request_obj['method'],
                        params=request_obj.get('params'),
                    )
                    send_rpc_message(
                        conn,
                        result_message(request, {'wire': 'pipeline'}),
                        RPC_DEFAULT_MAX_FRAME_BYTES,
                    )
            except BaseException as exc:  # noqa
                errors.append(exc)

        thread = threading.Thread(target=serve)
        thread.start()
        try:
            client = RpcClient(RpcClient.Config(
                socket_path=socket_path,
                io_timeout_s=TEST_TIMEOUT_S,
            ))
            assert client.call('echo') == {'wire': 'pipeline'}
        finally:
            listener.close()
            thread.join(TEST_TIMEOUT_S)

        assert not thread.is_alive()
        assert not errors
