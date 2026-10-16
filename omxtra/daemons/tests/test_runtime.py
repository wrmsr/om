import json
import os
import signal
import tempfile

from ..daemon import Daemon
from ..runtime import ServiceRuntime
from ..services import ServiceDaemon
from ..spawning import MultiprocessingSpawning
from .runtimehelper import RuntimeControlledService
from .testing import TEST_TIMEOUT_S
from .testing import accept_worker
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import make_unix_listener
from .testing import read_locked_pidfile
from .testing import receive_json_line
from .testing import wait_pidfile_unlocked


##


def _make_service_daemon(
        control_path: str,
        pid_file: str,
        runtime_config: ServiceRuntime.Config,
) -> ServiceDaemon[RuntimeControlledService, RuntimeControlledService.Config]:
    return ServiceDaemon(
        RuntimeControlledService.Config(
            runtime=runtime_config,
            control_path=control_path,
        ),
        Daemon.Config(
            spawning=MultiprocessingSpawning(
                start_method=MultiprocessingSpawning.StartMethod.SPAWN,
            ),
            pid_file=pid_file,
        ),
    )


def _send_command(conn, command: str):
    conn.sendall(json.dumps({'command': command}).encode('utf-8') + b'\n')
    return receive_json_line(conn)


def _wait_closed(conn) -> None:
    while conn.recv(4096):
        pass


def _kill_process(process) -> None:
    if process.is_alive():
        process.kill()
    process.join(TEST_TIMEOUT_S)
    process.close()


def test_runtime_service_exits_after_idle_timeout():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'service.pid')

        process = None
        with make_unix_listener(control_path) as listener:
            try:
                daemon = _make_service_daemon(
                    control_path,
                    pid_file,
                    ServiceRuntime.Config(idle_timeout_s=.1),
                ).daemon_()
                assert daemon.launch_no_wait()

                conn, info = accept_worker(listener)
                with conn:
                    process = find_multiprocessing_child(info['pid'])

                    assert receive_json_line(conn) == {
                        'event': 'SHUTDOWN',
                        'reason': 'IDLE',
                        'signal': None,
                    }
                    assert receive_json_line(conn) == {'event': 'EXITING'}
                    _wait_closed(conn)

                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(process) == 0
                process = None

            finally:
                if process is not None:
                    _kill_process(process)


def test_activity_blocks_idle_shutdown_and_starts_fresh_linger_window():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'service.pid')

        process = None
        with make_unix_listener(control_path) as listener:
            try:
                daemon = _make_service_daemon(
                    control_path,
                    pid_file,
                    ServiceRuntime.Config(idle_timeout_s=.1),
                ).daemon_()
                assert daemon.launch_no_wait()

                conn, info = accept_worker(listener)
                with conn:
                    process = find_multiprocessing_child(info['pid'])

                    assert _send_command(conn, 'START') == {
                        'event': 'ACTIVE',
                        'count': 1,
                    }
                    assert _send_command(conn, 'WAIT_IDLE_WINDOW') == {
                        'event': 'IDLE_WINDOW',
                        'shutdown': False,
                    }
                    assert _send_command(conn, 'FINISH') == {
                        'event': 'ACTIVE',
                        'count': 0,
                    }

                    assert receive_json_line(conn)['reason'] == 'IDLE'
                    assert receive_json_line(conn) == {'event': 'EXITING'}
                    _wait_closed(conn)

                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(process) == 0
                process = None

            finally:
                if process is not None:
                    _kill_process(process)


def test_sigterm_requests_shutdown_rejects_work_and_drains_activity():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'service.pid')

        process = None
        with make_unix_listener(control_path) as listener:
            try:
                daemon = _make_service_daemon(
                    control_path,
                    pid_file,
                    ServiceRuntime.Config(),
                ).daemon_()
                assert daemon.launch_no_wait()

                conn, info = accept_worker(listener)
                with conn:
                    worker_pid = info['pid']
                    process = find_multiprocessing_child(worker_pid)

                    assert _send_command(conn, 'START')['count'] == 1
                    os.kill(worker_pid, signal.SIGTERM)

                    assert receive_json_line(conn) == {
                        'event': 'SHUTDOWN',
                        'reason': 'SIGNAL',
                        'signal': signal.SIGTERM,
                    }
                    assert read_locked_pidfile(pid_file) == worker_pid

                    assert _send_command(conn, 'START') == {
                        'event': 'REJECTED',
                        'reason': 'SIGNAL',
                    }
                    assert _send_command(conn, 'FINISH') == {
                        'event': 'ACTIVE',
                        'count': 0,
                    }
                    assert receive_json_line(conn) == {'event': 'EXITING'}
                    _wait_closed(conn)

                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(process) == 0
                process = None

            finally:
                if process is not None:
                    _kill_process(process)


def test_runtime_service_enforces_drain_timeout():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'service.pid')

        process = None
        with make_unix_listener(control_path) as listener:
            try:
                daemon = _make_service_daemon(
                    control_path,
                    pid_file,
                    ServiceRuntime.Config(drain_timeout_s=.1),
                ).daemon_()
                assert daemon.launch_no_wait()

                conn, info = accept_worker(listener)
                with conn:
                    process = find_multiprocessing_child(info['pid'])
                    assert _send_command(conn, 'RETURN_ACTIVE') == {'event': 'RETURNING'}
                    _wait_closed(conn)

                wait_pidfile_unlocked(pid_file)
                assert join_multiprocessing_child(process) == 1
                process = None

            finally:
                if process is not None:
                    _kill_process(process)
