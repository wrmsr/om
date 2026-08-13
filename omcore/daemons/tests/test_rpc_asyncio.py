import asyncio
import os
import tempfile
import threading
import time
import typing as ta

import pytest

from ..rpc import AsyncioRpcClient
from ..rpc import AsyncioRpcServer
from ..rpc import AsyncioRpcServerConfig
from ..rpc import RpcClient
from ..rpc import RpcRemoteError
from ..rpc import RpcRequest
from ..rpc import RpcServer
from ..rpc import RpcServerConfig
from ..rpc import SimpleRpcServerRuntime
from ..rpc import ThreadedAsyncRpcHandler
from .testing import TEST_TIMEOUT_S


##


class _AsyncHandler:
    def __init__(self) -> None:
        super().__init__()

        self.calls: list[str] = []

    async def __call__(self, request: RpcRequest) -> ta.Any:
        self.calls.append(request.request_id)
        await asyncio.sleep(.01)
        if request.method == 'fail':
            raise RuntimeError(str(request.params))
        if request.method == 'empty-error':
            raise RuntimeError
        return request.params


def test_asyncio_rpc_server_rejects_implicit_sync_handler():
    def handler(request: RpcRequest) -> ta.Any:
        return request.params

    with pytest.raises(RuntimeError, match='ThreadedAsyncRpcHandler'):
        AsyncioRpcServerConfig(
            socket_path='/unused',
            handler=handler,
        )


def test_asyncio_rpc_client_server_concurrency_replay_and_remote_error():
    async def run() -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = os.path.join(temp_dir, 'rpc.sock')
            handler = _AsyncHandler()
            server = AsyncioRpcServer(AsyncioRpcServerConfig(
                socket_path=socket_path,
                handler=handler,
                connection_timeout_s=TEST_TIMEOUT_S,
                drain_timeout_s=TEST_TIMEOUT_S,
            ))
            await server.start()
            try:
                client = AsyncioRpcClient(RpcClient.Config(
                    socket_path=socket_path,
                    connect_timeout_s=TEST_TIMEOUT_S,
                    io_timeout_s=TEST_TIMEOUT_S,
                ))
                assert await client.ping() == server.instance_id

                results = await asyncio.gather(*(
                    client.call('echo', {'value': value})
                    for value in range(8)
                ))
                assert {result['value'] for result in results} == set(range(8))

                request = client.new_request(
                    'echo',
                    {'value': 'once'},
                    request_id='replayed-request',
                )
                assert await asyncio.gather(
                    client.call_request(request),
                    client.call_request(request),
                ) == [
                    {'value': 'once'},
                    {'value': 'once'},
                ]
                assert await client.call_request(request) == {'value': 'once'}
                assert handler.calls.count('replayed-request') == 1

                with pytest.raises(RpcRemoteError) as exc_info:
                    await client.call('fail', 'boom')
                assert exc_info.value.remote_type == 'builtins.RuntimeError'
                assert exc_info.value.message == 'boom'

                with pytest.raises(RpcRemoteError) as empty_exc_info:
                    await client.call('empty-error')
                assert empty_exc_info.value.message == ''
            finally:
                await server.close()

            assert not os.path.exists(socket_path)

    asyncio.run(run())


def test_asyncio_rpc_threaded_handler_policy_is_explicit_and_off_loop():
    async def run() -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = os.path.join(temp_dir, 'rpc.sock')
            loop_thread_id = threading.get_ident()
            handler_thread_ids: list[int] = []

            def handler(request: RpcRequest) -> ta.Any:
                handler_thread_ids.append(threading.get_ident())
                time.sleep(.01)
                return request.params

            async with AsyncioRpcServer(AsyncioRpcServerConfig(
                    socket_path=socket_path,
                    handler=ThreadedAsyncRpcHandler(handler),
                    connection_timeout_s=TEST_TIMEOUT_S,
                    drain_timeout_s=TEST_TIMEOUT_S,
            )):
                client = AsyncioRpcClient(RpcClient.Config(
                    socket_path=socket_path,
                    io_timeout_s=TEST_TIMEOUT_S,
                ))
                assert await client.call('echo', 'value') == 'value'

            assert len(handler_thread_ids) == 1
            assert handler_thread_ids[0] != loop_thread_id

    asyncio.run(run())


def test_asyncio_rpc_server_close_drains_an_accepted_request():
    async def run() -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = os.path.join(temp_dir, 'rpc.sock')
            started = asyncio.Event()
            release = asyncio.Event()

            async def handler(request: RpcRequest) -> ta.Any:
                started.set()
                await release.wait()
                return request.params

            server = AsyncioRpcServer(AsyncioRpcServerConfig(
                socket_path=socket_path,
                handler=handler,
                connection_timeout_s=TEST_TIMEOUT_S,
                drain_timeout_s=TEST_TIMEOUT_S,
            ))
            await server.start()
            client = AsyncioRpcClient(RpcClient.Config(
                socket_path=socket_path,
                io_timeout_s=TEST_TIMEOUT_S,
            ))

            call_task = asyncio.create_task(client.call('block', 'accepted'))
            await asyncio.wait_for(started.wait(), TEST_TIMEOUT_S)
            close_task = asyncio.create_task(server.close())
            await asyncio.sleep(.01)
            assert not close_task.done()

            release.set()
            assert await call_task == 'accepted'
            assert await close_task
            assert not os.path.exists(socket_path)

    asyncio.run(run())


def test_sync_client_interoperates_with_asyncio_server():
    async def run() -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = os.path.join(temp_dir, 'rpc.sock')
            async with AsyncioRpcServer(AsyncioRpcServerConfig(
                    socket_path=socket_path,
                    handler=_AsyncHandler(),
                    connection_timeout_s=TEST_TIMEOUT_S,
                    drain_timeout_s=TEST_TIMEOUT_S,
            )):
                client = RpcClient(RpcClient.Config(
                    socket_path=socket_path,
                    io_timeout_s=TEST_TIMEOUT_S,
                ))
                assert await asyncio.to_thread(client.call, 'echo', {'runtime': 'sync'}) == {
                    'runtime': 'sync',
                }

    asyncio.run(run())


def test_asyncio_client_interoperates_with_sync_server():
    async def run() -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = os.path.join(temp_dir, 'rpc.sock')

            def handler(request: RpcRequest) -> ta.Any:
                return request.params

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
                for _ in range(100):
                    if os.path.exists(socket_path):
                        break
                    await asyncio.sleep(.01)
                else:
                    raise TimeoutError('Synchronous RPC server did not bind')

                client = AsyncioRpcClient(RpcClient.Config(
                    socket_path=socket_path,
                    io_timeout_s=TEST_TIMEOUT_S,
                ))
                assert await client.call('echo', {'runtime': 'asyncio'}) == {
                    'runtime': 'asyncio',
                }
            finally:
                runtime.request_shutdown()
                await asyncio.to_thread(thread.join, TEST_TIMEOUT_S)

            assert not thread.is_alive()
            assert not errors

    asyncio.run(run())
