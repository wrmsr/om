import json
import os
import queue
import signal
import socket
import tempfile
import threading
import time
import urllib.request

import pytest

from ...daemon import Daemon
from ...httpwaiting import HttpWait
from ...runtime import ServiceRuntime
from ...runtime import ShutdownReason
from ...services import ServiceDaemon
from ...spawning import MultiprocessingSpawning
from ...tests.testing import TEST_TIMEOUT_S
from ...tests.testing import find_multiprocessing_child
from ...tests.testing import join_multiprocessing_child
from ...tests.testing import read_locked_pidfile
from ...tests.testing import wait_pidfile_unlocked
from ..configs import ChildProcessConfig
from ..configs import ChildProcessOutput
from ..configs import ChildProcessOutputMode
from ..configs import ChildTerminationConfig
from ..services import ChildProcessService
from ..supervisors import ChildProcessExitedError
from ..supervisors import ChildProcessResult
from ..supervisors import ChildProcessSupervisor
from ..supervisors import ChildProcessSupervisorConfig


##


def _python_cmd(*args: str) -> tuple[str, ...]:
    return (
        os.path.abspath('python'),
        '-m',
        'omcore.daemons.children.tests.helper',
        *args,
    )


def _read_events(path: str) -> list[dict]:
    try:
        with open(path) as file:
            return [json.loads(line) for line in file if line.strip()]
    except FileNotFoundError:
        return []


def _wait_event(path: str, event: str, *, role: str = 'child') -> dict:
    deadline = time.monotonic() + TEST_TIMEOUT_S
    while time.monotonic() < deadline:
        for item in _read_events(path):
            if item['event'] == event and item['role'] == role:
                return item
        time.sleep(.01)
    raise TimeoutError(f'Event {event!r} for {role!r} not written to {path!r}')


def _run_supervisor(
        supervisor: ChildProcessSupervisor,
        runtime: ServiceRuntime,
        outcomes: queue.Queue,
) -> None:
    try:
        outcomes.put(supervisor.run(runtime))
    except BaseException as exc:  # noqa
        outcomes.put(exc)


def _assert_process_gone(pid: int) -> None:
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def _reserve_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


##


@pytest.mark.skip(reason='FIXME')
def test_supervisor_forwards_shutdown_reaps_and_owns_descriptors() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        event_file = os.path.join(temp_dir, 'events.jsonl')
        stdout_file = os.path.join(temp_dir, 'stdout.log')
        stderr_file = os.path.join(temp_dir, 'stderr.log')
        read_fd, write_fd = os.pipe()

        supervisor = ChildProcessSupervisor(ChildProcessSupervisorConfig(
            process=ChildProcessConfig(
                cmd=_python_cmd(
                    '--event-file', event_file,
                    '--write-fd', str(write_fd),
                ),
                cwd=temp_dir,
                env={'OMCORE_DAEMONS_CHILD_TEST': 'configured'},
                stdout=ChildProcessOutput.file(stdout_file),
                stderr=ChildProcessOutput.file(stderr_file, append=False),
                pass_fds=(write_fd,),
            ),
            termination=ChildTerminationConfig(grace_timeout_s=1.),
        ))

        outcomes: queue.Queue = queue.Queue()
        try:
            with ServiceRuntime(ServiceRuntime.Config(no_signals=True)) as runtime:
                thread = threading.Thread(
                    target=_run_supervisor,
                    args=(supervisor, runtime, outcomes),
                )
                thread.start()

                started = _wait_event(event_file, 'STARTED')
                assert started['cwd'] == temp_dir
                assert started['test_env'] == 'configured'
                os.close(write_fd)
                write_fd = -1
                assert os.read(read_fd, 64) == b'passed-fd'

                assert runtime.shutdown.request(message='test-shutdown')
                result = outcomes.get(timeout=TEST_TIMEOUT_S)
                thread.join(TEST_TIMEOUT_S)

            assert isinstance(result, ChildProcessResult)
            assert result.pid == started['pid']
            assert result.returncode == 0
            assert result.shutdown_request is not None
            assert result.shutdown_request.message == 'test-shutdown'
            assert not result.escalated
            _assert_process_gone(result.pid)

            with open(stdout_file) as file:
                assert 'child-stdout:child' in file.read()
            with open(stderr_file) as file:
                assert 'child-stderr:child' in file.read()
            assert _wait_event(event_file, 'SIGNAL')['signal'] == signal.SIGTERM
            _wait_event(event_file, 'EXITING')

        finally:
            os.close(read_fd)
            if write_fd >= 0:
                os.close(write_fd)


def test_supervisor_escalates_an_ignored_graceful_signal() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        event_file = os.path.join(temp_dir, 'events.jsonl')
        supervisor = ChildProcessSupervisor(ChildProcessSupervisorConfig(
            process=ChildProcessConfig(cmd=_python_cmd(
                '--event-file', event_file,
                '--ignore-signal',
            )),
            termination=ChildTerminationConfig(
                grace_timeout_s=.1,
                kill_timeout_s=1.,
            ),
        ))

        outcomes: queue.Queue = queue.Queue()
        with ServiceRuntime(ServiceRuntime.Config(no_signals=True)) as runtime:
            thread = threading.Thread(
                target=_run_supervisor,
                args=(supervisor, runtime, outcomes),
            )
            thread.start()
            started = _wait_event(event_file, 'STARTED')

            runtime.shutdown.request()
            result = outcomes.get(timeout=TEST_TIMEOUT_S)
            thread.join(TEST_TIMEOUT_S)

        assert isinstance(result, ChildProcessResult)
        assert result.returncode == -signal.SIGKILL
        assert result.escalated
        assert _wait_event(event_file, 'SIGNAL')['signal'] == signal.SIGTERM
        _assert_process_gone(started['pid'])


def test_supervisor_signals_an_explicit_child_process_group() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        event_file = os.path.join(temp_dir, 'events.jsonl')
        supervisor = ChildProcessSupervisor(ChildProcessSupervisorConfig(
            process=ChildProcessConfig(
                cmd=_python_cmd('--event-file', event_file, '--spawn-grandchild'),
                start_new_session=True,
            ),
            termination=ChildTerminationConfig(
                signal_process_group=True,
                grace_timeout_s=2.,
            ),
        ))

        outcomes: queue.Queue = queue.Queue()
        with ServiceRuntime(ServiceRuntime.Config(no_signals=True)) as runtime:
            thread = threading.Thread(
                target=_run_supervisor,
                args=(supervisor, runtime, outcomes),
            )
            thread.start()
            started = _wait_event(event_file, 'STARTED')
            grandchild = _wait_event(event_file, 'STARTED', role='grandchild')
            assert started['pgid'] == started['pid']
            assert grandchild['pgid'] == started['pid']

            runtime.shutdown.request(ShutdownReason.SIGNAL, signal=signal.SIGINT)
            result = outcomes.get(timeout=TEST_TIMEOUT_S)
            thread.join(TEST_TIMEOUT_S)

        assert isinstance(result, ChildProcessResult)
        assert result.returncode == 0
        assert not result.escalated
        assert _wait_event(event_file, 'SIGNAL', role='child')['signal'] == signal.SIGINT
        assert _wait_event(event_file, 'SIGNAL', role='grandchild')['signal'] == signal.SIGINT
        _assert_process_gone(started['pid'])
        _assert_process_gone(grandchild['pid'])


def test_supervisor_propagates_unexpected_exit_and_requests_shutdown() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        event_file = os.path.join(temp_dir, 'events.jsonl')
        supervisor = ChildProcessSupervisor(ChildProcessSupervisorConfig(
            process=ChildProcessConfig(cmd=_python_cmd(
                '--event-file', event_file,
                '--exit-code', '7',
            )),
        ))

        with ServiceRuntime(ServiceRuntime.Config(no_signals=True)) as runtime:
            with pytest.raises(ChildProcessExitedError) as exc_info:
                supervisor.run(runtime)

            assert runtime.shutdown.requested
            request = runtime.shutdown.request_
            assert request is not None
            assert request.reason is ShutdownReason.REQUESTED

        result = exc_info.value.result
        assert result.returncode == 7
        assert result.shutdown_request is None
        _assert_process_gone(result.pid)


def test_supervisor_observes_exec_failure() -> None:
    supervisor = ChildProcessSupervisor(ChildProcessSupervisorConfig(
        process=ChildProcessConfig(cmd=('/definitely/not/a/real/executable',)),
    ))
    with ServiceRuntime(ServiceRuntime.Config(no_signals=True)) as runtime:
        with pytest.raises(FileNotFoundError):
            supervisor.run(runtime)
        assert runtime.shutdown.requested


@pytest.mark.skip(reason='FIXME')
def test_child_process_service_composes_with_http_wait_and_daemon_pidfile() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        event_file = os.path.join(temp_dir, 'events.jsonl')
        pid_file = os.path.join(temp_dir, 'supervisor.pid')
        output_file = os.path.join(temp_dir, 'child.log')
        port = _reserve_port()

        service = ChildProcessService.Config(
            process=ChildProcessConfig(
                cmd=_python_cmd(
                    '--event-file', event_file,
                    '--port', str(port),
                ),
                stdout=ChildProcessOutput.file(output_file),
                stderr=ChildProcessOutput(mode=ChildProcessOutputMode.STDOUT),
            ),
            termination=ChildTerminationConfig(grace_timeout_s=2.),
        )
        daemon = ServiceDaemon(
            service,
            Daemon.Config(
                spawning=MultiprocessingSpawning(
                    start_method=MultiprocessingSpawning.StartMethod.SPAWN,
                ),
                pid_file=pid_file,
                wait=HttpWait(
                    url=f'http://127.0.0.1:{port}/healthz',
                    expected_body=b'healthy',
                ),
                wait_timeout=TEST_TIMEOUT_S,
                wait_sleep_s=.01,
            ),
        ).daemon_()

        process = None
        child_pid = None
        try:
            daemon.launch()
            supervisor_pid = read_locked_pidfile(pid_file)
            process = find_multiprocessing_child(supervisor_pid)

            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(f'http://127.0.0.1:{port}/pid', timeout=TEST_TIMEOUT_S) as response:
                child_pid = int(response.read())
            assert child_pid != supervisor_pid

            os.kill(supervisor_pid, signal.SIGTERM)
            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(process) == 0
            process = None

            assert _wait_event(event_file, 'SIGNAL')['signal'] == signal.SIGTERM
            _assert_process_gone(child_pid)

        finally:
            if process is not None:
                if process.is_alive():
                    os.kill(process.pid, signal.SIGTERM)
                    process.join(2.)
                if process.is_alive():
                    process.kill()
                    process.join(TEST_TIMEOUT_S)
                process.close()
            if child_pid is not None:
                try:
                    os.kill(child_pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
