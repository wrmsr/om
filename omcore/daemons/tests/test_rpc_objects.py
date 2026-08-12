import abc
import os
import tempfile
import threading
import time

import pytest

from ..rpc import RpcClient
from ..rpc import RpcObjectHandler
from ..rpc import RpcObjectProxy
from ..rpc import RpcRemoteError
from ..rpc import RpcServer
from ..rpc import RpcServerConfig
from ..rpc import RpcUnavailableError
from ..rpc import SimpleRpcServerRuntime
from ..rpc import rpc_method
from .testing import TEST_TIMEOUT_S


##


class Calculator(abc.ABC):
    @rpc_method
    @abc.abstractmethod
    def add(self, left: int, right: int = 1) -> int:
        raise NotImplementedError

    @rpc_method(name='describe')
    @abc.abstractmethod
    def label(self, *, prefix: str) -> str:
        raise NotImplementedError

    def local_only(self) -> str:
        return 'local'


class CalculatorImpl(Calculator):
    def __init__(self) -> None:
        super().__init__()

        self.calls: list[tuple[str, object]] = []

    def add(self, left: int, right: int = 1) -> int:
        self.calls.append(('add', (left, right)))
        return left + right

    def label(self, *, prefix: str) -> str:
        self.calls.append(('label', prefix))
        return f'{prefix}: calculator'


def test_rpc_object_facade_over_decoupled_thread_server():
    with tempfile.TemporaryDirectory() as temp_dir:
        socket_path = os.path.join(temp_dir, 'object.sock')
        implementation = CalculatorImpl()
        runtime = SimpleRpcServerRuntime(drain_timeout_s=TEST_TIMEOUT_S)
        server = RpcServer(RpcServerConfig(
            socket_path=socket_path,
            handler=RpcObjectHandler(
                Calculator,
                implementation,
                namespace='calculator',
            ),
            connection_timeout_s=TEST_TIMEOUT_S,
        ))
        client = RpcClient(RpcClient.Config(
            socket_path=socket_path,
            connect_timeout_s=.1,
            io_timeout_s=TEST_TIMEOUT_S,
        ))
        calculator: Calculator = RpcObjectProxy.of(Calculator, client, namespace='calculator')

        assert isinstance(calculator, Calculator)
        assert calculator.local_only() == 'local'

        # Signature binding happens locally, before any connection or handler invocation.
        with pytest.raises(TypeError):
            calculator.add()  # type: ignore[call-arg]
        assert implementation.calls == []

        errors: list[BaseException] = []

        def run_server() -> None:
            try:
                server.run(runtime)
            except BaseException as exc:  # noqa
                errors.append(exc)

        thread = threading.Thread(target=run_server, name='RpcObjectTestServer')
        thread.start()
        try:
            deadline = time.monotonic() + TEST_TIMEOUT_S
            while True:
                try:
                    client.ping()
                except RpcUnavailableError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(.01)
                else:
                    break

            assert calculator.add(4) == 5
            assert calculator.add(4, right=3) == 7
            assert calculator.label(prefix='remote') == 'remote: calculator'
            assert implementation.calls == [
                ('add', (4, 1)),
                ('add', (4, 3)),
                ('label', 'remote'),
            ]

            with pytest.raises(RpcRemoteError, match='Unknown RPC object method'):
                client.call('calculator.local_only', {'args': [], 'kwargs': {}})

        finally:
            runtime.request_shutdown()
            thread.join(TEST_TIMEOUT_S)

        assert not thread.is_alive()
        assert errors == []
        assert not os.path.exists(socket_path)
