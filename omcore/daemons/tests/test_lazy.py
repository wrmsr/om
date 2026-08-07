import concurrent.futures
import functools
import json
import multiprocessing as mp
import os
import socket
import tempfile
import threading
import typing as ta

from ... import check
from ..daemon import Daemon
from ..lazy import LazyDaemon
from ..runtime import ServiceRuntime
from ..services import ServiceDaemon
from ..spawning import MultiprocessingSpawning
from ..waiting import FnWait
from .lazyhelper import LazySocketService
from .testing import TEST_TIMEOUT_S
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import receive_json_line
from .testing import wait_pidfile_unlocked


##


class _WorkerUnavailableError(RuntimeError):
    pass


def _can_connect(socket_path: str) -> bool:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        try:
            sock.connect(socket_path)
        except (ConnectionRefusedError, FileNotFoundError):
            return False
        else:
            return True


def _request(socket_path: str, command: str, value: ta.Any = None) -> ta.Mapping[str, ta.Any]:
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(TEST_TIMEOUT_S)
            sock.connect(socket_path)
            sock.sendall(json.dumps({
                'command': command,
                'value': value,
            }).encode('utf-8') + b'\n')
            return receive_json_line(sock)
    except (BrokenPipeError, ConnectionError, FileNotFoundError, RuntimeError, TimeoutError) as exc:
        raise _WorkerUnavailableError from exc


def _is_unavailable(exc: Exception) -> bool:
    return isinstance(exc, _WorkerUnavailableError)


def _make_lazy_daemon(temp_dir: str) -> tuple[LazyDaemon, str, str, str]:
    socket_path = os.path.join(temp_dir, 'lazy.sock')
    pid_file = os.path.join(temp_dir, 'lazy.pid')
    launch_log = os.path.join(temp_dir, 'launches.jsonl')

    service_daemon: ServiceDaemon[LazySocketService, LazySocketService.Config] = ServiceDaemon(
        LazySocketService.Config(
            runtime=ServiceRuntime.Config(idle_timeout_s=.2),
            socket_path=socket_path,
            launch_log=launch_log,
        ),
        Daemon.Config(
            spawning=MultiprocessingSpawning(
                start_method=MultiprocessingSpawning.StartMethod.SPAWN,
            ),
            pid_file=pid_file,
            wait=FnWait(functools.partial(_can_connect, socket_path)),
            wait_timeout=TEST_TIMEOUT_S,
            wait_sleep_s=.01,
        ),
    )

    return LazyDaemon(service_daemon.daemon_()), socket_path, pid_file, launch_log


def _read_launches(path: str) -> list[ta.Mapping[str, ta.Any]]:
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


def test_lazy_daemon_coalesces_concurrent_calls_and_lingers():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        lazy, socket_path, pid_file, launch_log = _make_lazy_daemon(temp_dir)

        try:
            num_callers = 8
            barrier = threading.Barrier(num_callers)

            def call(value: int) -> ta.Mapping[str, ta.Any]:
                barrier.wait()
                return lazy.call(
                    functools.partial(_request, socket_path, 'PING', value),
                    is_unavailable=_is_unavailable,
                )

            with concurrent.futures.ThreadPoolExecutor(max_workers=num_callers) as executor:
                responses = list(executor.map(call, range(num_callers)))

            assert {response['value'] for response in responses} == set(range(num_callers))
            assert len({response['instance'] for response in responses}) == 1
            assert len({response['pid'] for response in responses}) == 1

            worker_pid = check.isinstance(responses[0]['pid'], int)
            process = find_multiprocessing_child(worker_pid)

            assert _read_launches(launch_log) == [{
                'instance': responses[0]['instance'],
                'pid': worker_pid,
            }]

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(process) == 0

        finally:
            _cleanup_new_children(prior_child_pids)


def test_lazy_daemon_relaunches_across_shutdown_race():
    prior_child_pids = {check.isinstance(process.pid, int) for process in mp.active_children()}

    with tempfile.TemporaryDirectory() as temp_dir:
        lazy, socket_path, pid_file, launch_log = _make_lazy_daemon(temp_dir)

        try:
            first = lazy.call(
                functools.partial(_request, socket_path, 'PING', 'first'),
                is_unavailable=_is_unavailable,
            )
            first_process = find_multiprocessing_child(first['pid'])

            shutdown = lazy.call(
                functools.partial(_request, socket_path, 'SHUTDOWN'),
                is_unavailable=_is_unavailable,
            )
            assert shutdown['instance'] == first['instance']

            second = lazy.call(
                functools.partial(_request, socket_path, 'PING', 'second'),
                is_unavailable=_is_unavailable,
            )
            second_process = find_multiprocessing_child(second['pid'])

            assert second['instance'] != first['instance']
            assert join_multiprocessing_child(first_process) == 0

            launches = _read_launches(launch_log)
            assert [launch['instance'] for launch in launches] == [
                first['instance'],
                second['instance'],
            ]

            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(second_process) == 0

        finally:
            _cleanup_new_children(prior_child_pids)
