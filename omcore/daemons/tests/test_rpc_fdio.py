import os
import tempfile
import threading
import time
import typing as ta

import pytest

from ..rpc import FdioRpcServer
from ..rpc import RpcClient
from ..rpc import RpcRemoteError
from ..rpc import RpcRequest
from ..rpc import RpcServerConfig
from ..rpc import SimpleRpcServerRuntime
from .testing import TEST_TIMEOUT_S


##


def test_fdio_rpc_server_real_unix_socket_replay_and_remote_error():
    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, 'rpc.sock')
        calls: list[str] = []

        def handler(request: RpcRequest) -> ta.Any:
            calls.append(request.request_id)
            if request.method == 'fail':
                raise RuntimeError(str(request.params))
            return request.params

        runtime = SimpleRpcServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
        server = FdioRpcServer(RpcServerConfig(
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
            deadline = time.monotonic() + TEST_TIMEOUT_S
            while not os.path.exists(socket_path):
                if time.monotonic() >= deadline:
                    raise TimeoutError('fdio RPC server did not bind')
                time.sleep(.01)

            client = RpcClient(RpcClient.Config(
                socket_path=socket_path,
                io_timeout_s=TEST_TIMEOUT_S,
            ))
            instance_id = client.ping()
            assert instance_id is not None

            request = client.new_request(
                'echo',
                {'value': 'once'},
                request_id='fdio-replay',
            )
            assert client.call_request(request) == {'value': 'once'}
            assert client.call_request(request) == {'value': 'once'}
            assert calls.count('fdio-replay') == 1

            with pytest.raises(RpcRemoteError) as exc_info:
                client.call('fail', 'boom')
            assert exc_info.value.remote_type == 'builtins.RuntimeError'
            assert exc_info.value.message == 'boom'
        finally:
            runtime.request_shutdown()
            thread.join(TEST_TIMEOUT_S)

        assert not thread.is_alive()
        assert not errors
        assert not os.path.exists(socket_path)
