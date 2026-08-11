import concurrent.futures
import json
import multiprocessing as mp
import os
import signal
import socket
import tempfile
import threading
import typing as ta
import uuid

import pytest

from ... import check
from ..daemon import Daemon
from ..lazy import LazyDaemon
from ..rpc import LazyRpcClient
from ..rpc import RpcCallIndeterminateError
from ..rpc import RpcClient
from ..rpc import RpcProtocolError
from ..rpc import RpcRemoteError
from ..rpc import RpcRequest
from ..rpc import RpcService
from ..rpc import RpcWait
from ..runtime import ServiceRuntime
from ..services import ServiceDaemon
from ..spawning import MultiprocessingSpawning
from .rpchelper import ControlledRpcHandler
from .testing import TEST_TIMEOUT_S
from .testing import accept_worker
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import make_unix_listener
from .testing import read_locked_daemon_pidfile_info
from .testing import read_locked_pidfile
from .testing import wait_pidfile_unlocked


##


def _recv_frame(sock: socket.socket) -> bytes:
    header = bytearray()
    while len(header) < 4:
        chunk = sock.recv(4 - len(header))
        if not chunk:
            raise EOFError
        header.extend(chunk)

    size = int.from_bytes(header, 'big')
    payload = bytearray()
    while len(payload) < size:
        chunk = sock.recv(size - len(payload))
        if not chunk:
            raise EOFError
        payload.extend(chunk)
    return bytes(header + payload)


class _DroppingRpcProxy:
    def __init__(self, socket_path: str, upstream_path: str) -> None:
        super().__init__()

        self._socket_path = socket_path
        self._upstream_path = upstream_path

        self._stop = threading.Event()
        self._dropped = threading.Event()
        self._forwarded = threading.Event()
        self._errors: list[BaseException] = []

        self._listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._listener.bind(socket_path)
        self._listener.listen()
        self._listener.settimeout(.1)

        self._thread = threading.Thread(
            target=self._run,
            name='DroppingRpcProxy',
            daemon=True,
        )
        self._thread.start()

    @property
    def dropped(self) -> bool:
        return self._dropped.is_set()

    @property
    def forwarded(self) -> bool:
        return self._forwarded.is_set()

    def _handle(self, downstream: socket.socket) -> None:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as upstream:
            try:
                upstream.connect(self._upstream_path)
            except (ConnectionRefusedError, FileNotFoundError):
                return

            upstream.sendall(_recv_frame(downstream))
            downstream.sendall(_recv_frame(upstream))

            upstream.sendall(_recv_frame(downstream))
            response = _recv_frame(upstream)

            if not self._dropped.is_set():
                self._dropped.set()
                return

            downstream.sendall(response)
            self._forwarded.set()

    def _run(self) -> None:
        try:
            while not self._stop.is_set() and not self._forwarded.is_set():
                try:
                    conn, _ = self._listener.accept()
                except TimeoutError:
                    continue
                except OSError:
                    if self._stop.is_set():
                        return
                    raise

                with conn:
                    self._handle(conn)

        except BaseException as exc:  # noqa
            self._errors.append(exc)

    def close(self) -> None:
        self._stop.set()
        self._listener.close()
        self._thread.join(TEST_TIMEOUT_S)
        if self._thread.is_alive():
            raise TimeoutError('Dropping RPC proxy did not stop')

        try:
            os.unlink(self._socket_path)
        except FileNotFoundError:
            pass

        if self._errors:
            raise self._errors[0]

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


##


def _make_rpc_clients(
        temp_dir: str,
        *,
        control_path: str | None = None,
) -> tuple[LazyRpcClient, RpcClient, LazyDaemon, str, str]:
    socket_path = os.path.join(temp_dir, 'rpc.sock')
    pid_file = os.path.join(temp_dir, 'rpc.pid')
    execution_log = os.path.join(temp_dir, 'executions.jsonl')

    client_config = RpcClient.Config(
        socket_path=socket_path,
        connect_timeout_s=1.,
        io_timeout_s=TEST_TIMEOUT_S,
    )
    service_daemon: ServiceDaemon[RpcService, RpcService.Config] = ServiceDaemon(
        RpcService.Config(
            runtime=ServiceRuntime.Config(
                idle_timeout_s=.2,
                drain_timeout_s=TEST_TIMEOUT_S,
            ),
            socket_path=socket_path,
            handler=ControlledRpcHandler(
                execution_log=execution_log,
                control_path=control_path,
            ),
            connection_timeout_s=TEST_TIMEOUT_S,
        ),
        Daemon.Config(
            spawning=MultiprocessingSpawning(
                start_method=MultiprocessingSpawning.StartMethod.SPAWN,
            ),
            pid_file=pid_file,
            wait=RpcWait(client_config),
            wait_timeout=TEST_TIMEOUT_S,
            wait_sleep_s=.01,
        ),
    )

    lazy_daemon = LazyDaemon(service_daemon.daemon_())
    client = RpcClient(client_config)
    return LazyRpcClient(lazy_daemon, client), client, lazy_daemon, pid_file, execution_log


def _read_executions(path: str) -> list[ta.Mapping[str, ta.Any]]:
    with open(path) as f:
        return [json.loads(line) for line in f]


def _cleanup_new_children(prior_child_pids: set[int]) -> None:
    for process in mp.active_children():
        if process.pid in prior_child_pids:
            continue
        if process.is_alive():
            process.terminate()
        process.join(TEST_TIMEOUT_S)
        process.close()


##


def test_lazy_rpc_concurrent_calls_remote_error_and_idle_exit():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        lazy_client, client, _, pid_file, execution_log = _make_rpc_clients(temp_dir)

        try:
            num_callers = 8
            barrier = threading.Barrier(num_callers)

            def call(value: int) -> ta.Mapping[str, ta.Any]:
                barrier.wait()
                return lazy_client.call('echo', {'value': value})

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_callers) as executor:
                responses = list(executor.map(call, range(num_callers)))

            assert {response['params']['value'] for response in responses} == set(range(num_callers))
            assert len({response['pid'] for response in responses}) == 1

            worker_pid = check.isinstance(responses[0]['pid'], int)
            process = find_multiprocessing_child(worker_pid)
            pidfile_info = read_locked_daemon_pidfile_info(pid_file)
            assert pidfile_info.pid == worker_pid
            assert isinstance(pidfile_info.instance_id, uuid.UUID)
            assert client.ping() == pidfile_info.instance_id

            with pytest.raises(RpcRemoteError) as exc_info:
                lazy_client.call('fail', 'boom')
            assert exc_info.value.remote_type == 'builtins.RuntimeError'
            assert exc_info.value.message == 'controlled failure: boom'

            executions = _read_executions(execution_log)
            assert len(executions) == num_callers + 1
            assert {execution['pid'] for execution in executions} == {worker_pid}

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(process) == 0

        finally:
            _cleanup_new_children(prior_child_pids)


def test_rpc_same_request_is_executed_once_after_response_is_abandoned():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        _, client, lazy_daemon, pid_file, execution_log = _make_rpc_clients(temp_dir)

        try:
            assert lazy_daemon.ensure()

            request = client.new_request(
                'echo',
                {'value': 'once'},
                request_id='controlled-request',
            )
            with client.connect() as conn:
                instance_id = conn.instance_id
                assert isinstance(instance_id, uuid.UUID)
                conn.send(request)

            result = client.call_request(
                request,
                expected_instance_id=instance_id,
            )
            assert result['params'] == {'value': 'once'}

            conflicting_request = RpcRequest(
                client_id=request.client_id,
                request_id=request.request_id,
                method=request.method,
                params={'value': 'different'},
            )
            with pytest.raises(RpcProtocolError, match='reused with different request data'):
                client.call_request(
                    conflicting_request,
                    expected_instance_id=instance_id,
                )

            worker_pid = check.isinstance(result['pid'], int)
            process = find_multiprocessing_child(worker_pid)

            executions = _read_executions(execution_log)
            assert [execution['request_id'] for execution in executions] == ['controlled-request']

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(process) == 0

        finally:
            _cleanup_new_children(prior_child_pids)


def test_lazy_rpc_replays_lost_response_on_same_instance():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        _, client, lazy_daemon, pid_file, execution_log = _make_rpc_clients(temp_dir)
        proxy_path = os.path.join(temp_dir, 'proxy.sock')

        try:
            with _DroppingRpcProxy(proxy_path, client.config.socket_path) as proxy:
                proxy_client = LazyRpcClient(
                    lazy_daemon,
                    RpcClient(RpcClient.Config(
                        socket_path=proxy_path,
                        connect_timeout_s=1.,
                        io_timeout_s=TEST_TIMEOUT_S,
                    )),
                )
                result = proxy_client.call('echo', {'value': 'retried'})

                assert proxy.dropped
                assert proxy.forwarded

            assert result['params'] == {'value': 'retried'}
            worker_pid = check.isinstance(result['pid'], int)
            process = find_multiprocessing_child(worker_pid)

            executions = _read_executions(execution_log)
            assert len(executions) == 1
            assert executions[0]['pid'] == worker_pid

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(process) == 0

        finally:
            _cleanup_new_children(prior_child_pids)


def test_rpc_activity_drains_and_lazy_call_relaunches_after_sigterm():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')

        with make_unix_listener(control_path) as control_listener:
            lazy_client, _, _, pid_file, _ = _make_rpc_clients(
                temp_dir,
                control_path=control_path,
            )

            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    blocked_future = executor.submit(lazy_client.call, 'block', 'held')

                    control_conn, block_info = accept_worker(control_listener)
                    with control_conn:
                        first_pid = check.isinstance(block_info['pid'], int)
                        first_process = find_multiprocessing_child(first_pid)
                        os.kill(first_pid, signal.SIGTERM)

                        replacement_future = executor.submit(lazy_client.call, 'echo', {'value': 'replacement'})

                        control_conn.sendall(b'X')

                    blocked_result = blocked_future.result(TEST_TIMEOUT_S)
                    replacement_result = replacement_future.result(TEST_TIMEOUT_S)

                assert blocked_result == {
                    'params': 'held',
                    'pid': first_pid,
                }
                assert replacement_result['params'] == {'value': 'replacement'}

                second_pid = check.isinstance(replacement_result['pid'], int)
                assert second_pid != first_pid
                second_process = find_multiprocessing_child(second_pid)

                assert join_multiprocessing_child(first_process) == 0
                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(second_process) == 0

            finally:
                _cleanup_new_children(prior_child_pids)


def test_rpc_refuses_to_replay_indeterminate_call_on_new_instance():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')

        with make_unix_listener(control_path) as control_listener:
            _, client, lazy_daemon, pid_file, execution_log = _make_rpc_clients(
                temp_dir,
                control_path=control_path,
            )

            try:
                assert lazy_daemon.ensure()

                request = client.new_request(
                    'block',
                    'indeterminate',
                    request_id='indeterminate-request',
                )
                conn = client.connect()
                first_instance_id = conn.instance_id
                conn.send(request)

                control_conn, block_info = accept_worker(control_listener)
                with control_conn:
                    first_pid = check.isinstance(block_info['pid'], int)
                    first_process = find_multiprocessing_child(first_pid)

                    conn.close()
                    os.kill(first_pid, signal.SIGTERM)
                    control_conn.sendall(b'X')

                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(first_process) == 0

                assert lazy_daemon.ensure()
                second_pid = read_locked_pidfile(pid_file)
                second_process = find_multiprocessing_child(second_pid)
                second_instance_id = client.ping()

                with pytest.raises(RpcCallIndeterminateError) as exc_info:
                    client.call_request(
                        request,
                        expected_instance_id=first_instance_id,
                    )

                error = exc_info.value
                assert error.request is request
                assert error.instance_id == first_instance_id
                assert error.actual_instance_id == second_instance_id

                executions = _read_executions(execution_log)
                assert [execution['request_id'] for execution in executions] == ['indeterminate-request']

                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(second_process) == 0

            finally:
                _cleanup_new_children(prior_child_pids)
