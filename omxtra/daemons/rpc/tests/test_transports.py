import asyncio
import socket
import threading
import typing as ta
import uuid

import pytest

from ...tests.testing import TEST_TIMEOUT_S
from .. import AsyncioRpcClient
from .. import AsyncioRpcServer
from .. import AsyncioRpcServerConfig
from .. import DefaultSyncRpcTransport
from .. import FdioRpcServer
from .. import RpcClient
from .. import RpcEndpoint
from .. import RpcRemoteError
from .. import RpcRequest
from .. import RpcServer
from .. import RpcServerConfig
from .. import RpcWait
from .. import RpcWaiter
from .. import SimpleRpcServerRuntime
from .. import SyncRpcListener
from .. import TcpRpcEndpoint
from .. import UnixRpcEndpoint


##


def _sync_handler(calls: list[str]):
    def handler(request: RpcRequest) -> ta.Any:
        calls.append(request.request_id)
        if request.method == 'fail':
            raise RuntimeError(str(request.params))
        return request.params

    return handler


def _async_handler(calls: list[str]):
    async def handler(request: RpcRequest) -> ta.Any:
        calls.append(request.request_id)
        if request.method == 'fail':
            raise RuntimeError(str(request.params))
        return request.params

    return handler


class _RecordingSyncRpcTransport:
    def __init__(self) -> None:
        super().__init__()

        self._delegate = DefaultSyncRpcTransport()
        self.connect_endpoints: list[RpcEndpoint] = []
        self.listen_endpoints: list[RpcEndpoint] = []

    def connect(
            self,
            endpoint: RpcEndpoint,
            *,
            timeout_s: float | None,
    ) -> socket.socket:
        self.connect_endpoints.append(endpoint)
        return self._delegate.connect(endpoint, timeout_s=timeout_s)

    def listen(
            self,
            endpoint: RpcEndpoint,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> SyncRpcListener:
        self.listen_endpoints.append(endpoint)
        return self._delegate.listen(
            endpoint,
            backlog=backlog,
            unix_socket_mode=unix_socket_mode,
        )


def _start_sync_server(
        server: RpcServer | FdioRpcServer,
        runtime: SimpleRpcServerRuntime,
        instance_id: uuid.UUID,
) -> tuple[threading.Thread, list[BaseException]]:
    errors: list[BaseException] = []

    def serve() -> None:
        try:
            server.run(runtime, instance_id=instance_id)
        except BaseException as exc:  # noqa
            errors.append(exc)

    thread = threading.Thread(target=serve, name='TcpRpcTestServer')
    thread.start()
    assert server.wait_started(TEST_TIMEOUT_S)
    return thread, errors


def _stop_sync_server(
        runtime: SimpleRpcServerRuntime,
        thread: threading.Thread,
        errors: list[BaseException],
) -> None:
    runtime.request_shutdown()
    thread.join(TEST_TIMEOUT_S)
    assert not thread.is_alive()
    assert not errors


def _tcp_client_config(endpoint: TcpRpcEndpoint) -> RpcClient.Config:
    return RpcClient.Config(
        endpoint=endpoint,
        connect_timeout_s=TEST_TIMEOUT_S,
        io_timeout_s=TEST_TIMEOUT_S,
    )


##


def test_rpc_endpoint_config_preserves_unix_socket_path_compatibility():
    unix_config = RpcClient.Config(socket_path='/example.sock')
    assert unix_config.resolved_endpoint == UnixRpcEndpoint(path='/example.sock')

    tcp_endpoint = TcpRpcEndpoint(host='127.0.0.1', port=12345)
    tcp_config = RpcClient.Config(endpoint=tcp_endpoint)
    assert tcp_config.resolved_endpoint is tcp_endpoint

    with pytest.raises(RuntimeError, match='Specify either endpoint or socket_path'):
        RpcClient.Config(
            socket_path='/example.sock',
            endpoint=tcp_endpoint,
        )


def test_sync_rpc_client_and_server_over_tcp_with_resolved_port_and_replay():
    calls: list[str] = []
    transport = _RecordingSyncRpcTransport()
    instance_id = uuid.uuid7()
    runtime = SimpleRpcServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
    configured_endpoint = TcpRpcEndpoint(host='127.0.0.1', port=0)
    server = RpcServer(RpcServerConfig(
        endpoint=configured_endpoint,
        handler=_sync_handler(calls),
        connection_timeout_s=TEST_TIMEOUT_S,
    ), transport=transport)
    thread, errors = _start_sync_server(server, runtime, instance_id)
    try:
        endpoint = server.bound_endpoint
        assert isinstance(endpoint, TcpRpcEndpoint)
        assert endpoint.host == '127.0.0.1'
        assert endpoint.port > 0

        client_config = _tcp_client_config(endpoint)
        assert RpcWaiter(RpcWait(client_config)).do_wait()
        client = RpcClient(client_config, transport=transport)
        assert client.ping() == instance_id
        request = client.new_request('echo', {'transport': 'tcp'}, request_id='sync-sync')
        assert client.call_request(request) == {'transport': 'tcp'}
        assert client.call_request(request) == {'transport': 'tcp'}
        assert calls.count('sync-sync') == 1
        assert transport.listen_endpoints == [configured_endpoint]
        assert transport.connect_endpoints == [endpoint, endpoint, endpoint]
    finally:
        _stop_sync_server(runtime, thread, errors)


def test_asyncio_rpc_client_interoperates_with_sync_tcp_server():
    async def run() -> None:
        calls: list[str] = []
        instance_id = uuid.uuid7()
        runtime = SimpleRpcServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
        server = RpcServer(RpcServerConfig(
            endpoint=TcpRpcEndpoint(host='127.0.0.1', port=0),
            handler=_sync_handler(calls),
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        thread, errors = _start_sync_server(server, runtime, instance_id)
        try:
            endpoint = server.bound_endpoint
            assert isinstance(endpoint, TcpRpcEndpoint)
            client = AsyncioRpcClient(_tcp_client_config(endpoint))
            assert await client.ping() == instance_id
            request = client.new_request('echo', 'async-sync', request_id='async-sync')
            assert await client.call_request(request) == 'async-sync'
            assert await client.call_request(request) == 'async-sync'
            assert calls.count('async-sync') == 1
        finally:
            await asyncio.to_thread(_stop_sync_server, runtime, thread, errors)

    asyncio.run(run())


def test_sync_rpc_client_interoperates_with_asyncio_tcp_server():
    async def run() -> None:
        calls: list[str] = []
        instance_id = uuid.uuid7()
        server = AsyncioRpcServer(AsyncioRpcServerConfig(
            endpoint=TcpRpcEndpoint(host='127.0.0.1', port=0),
            handler=_async_handler(calls),
            connection_timeout_s=TEST_TIMEOUT_S,
            drain_timeout_s=TEST_TIMEOUT_S,
        ))
        await server.start(instance_id=instance_id)
        try:
            endpoint = server.bound_endpoint
            assert isinstance(endpoint, TcpRpcEndpoint)
            client = RpcClient(_tcp_client_config(endpoint))
            assert await asyncio.to_thread(client.ping) == instance_id
            request = client.new_request('echo', 'sync-async', request_id='sync-async')
            assert await asyncio.to_thread(client.call_request, request) == 'sync-async'
            assert await asyncio.to_thread(client.call_request, request) == 'sync-async'
            assert calls.count('sync-async') == 1
        finally:
            await server.close()

    asyncio.run(run())


def test_asyncio_rpc_client_and_server_over_tcp_replay_and_remote_error():
    async def run() -> None:
        calls: list[str] = []
        instance_id = uuid.uuid7()
        server = AsyncioRpcServer(AsyncioRpcServerConfig(
            endpoint=TcpRpcEndpoint(host='127.0.0.1', port=0),
            handler=_async_handler(calls),
            connection_timeout_s=TEST_TIMEOUT_S,
            drain_timeout_s=TEST_TIMEOUT_S,
        ))
        await server.start(instance_id=instance_id)
        try:
            endpoint = server.bound_endpoint
            assert isinstance(endpoint, TcpRpcEndpoint)
            client = AsyncioRpcClient(_tcp_client_config(endpoint))
            assert await client.ping() == instance_id
            request = client.new_request('echo', 'async-async', request_id='async-async')
            assert await client.call_request(request) == 'async-async'
            assert await client.call_request(request) == 'async-async'
            assert calls.count('async-async') == 1

            with pytest.raises(RpcRemoteError) as exc_info:
                await client.call('fail', 'tcp failure')
            assert exc_info.value.remote_type == 'builtins.RuntimeError'
            assert exc_info.value.message == 'tcp failure'
        finally:
            await server.close()

    asyncio.run(run())


def test_asyncio_tcp_server_close_drains_accepted_request():
    async def run() -> None:
        started = asyncio.Event()
        release = asyncio.Event()

        async def handler(request: RpcRequest) -> ta.Any:
            started.set()
            await release.wait()
            return request.params

        server = AsyncioRpcServer(AsyncioRpcServerConfig(
            endpoint=TcpRpcEndpoint(host='127.0.0.1', port=0),
            handler=handler,
            connection_timeout_s=TEST_TIMEOUT_S,
            drain_timeout_s=TEST_TIMEOUT_S,
        ))
        await server.start()
        endpoint = server.bound_endpoint
        assert isinstance(endpoint, TcpRpcEndpoint)
        client = AsyncioRpcClient(_tcp_client_config(endpoint))

        call_task = asyncio.create_task(client.call('block', 'accepted'))
        await asyncio.wait_for(started.wait(), TEST_TIMEOUT_S)
        close_task = asyncio.create_task(server.close())
        await asyncio.sleep(.01)
        assert not close_task.done()

        release.set()
        assert await call_task == 'accepted'
        assert await close_task

    asyncio.run(run())


def test_fdio_rpc_server_uses_shared_tcp_listener_transport():
    calls: list[str] = []
    instance_id = uuid.uuid7()
    runtime = SimpleRpcServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
    server = FdioRpcServer(RpcServerConfig(
        endpoint=TcpRpcEndpoint(host='127.0.0.1', port=0),
        handler=_sync_handler(calls),
        connection_timeout_s=TEST_TIMEOUT_S,
    ))
    thread, errors = _start_sync_server(server, runtime, instance_id)
    try:
        endpoint = server.bound_endpoint
        assert isinstance(endpoint, TcpRpcEndpoint)
        client = RpcClient(_tcp_client_config(endpoint))
        assert client.ping() == instance_id
        assert client.call('echo', 'fdio-tcp') == 'fdio-tcp'
    finally:
        _stop_sync_server(runtime, thread, errors)
