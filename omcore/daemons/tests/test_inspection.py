import os
import signal
import socket
import tempfile

from ..children.configs import ChildProcessConfig
from ..children.configs import ChildProcessOutput
from ..children.configs import ChildProcessOutputMode
from ..children.configs import ChildTerminationConfig
from ..children.services import ChildProcessService
from ..daemon import Daemon
from ..httpwaiting import HttpWait
from ..inspection import DaemonInspector
from ..inspection import DaemonLifecycleState
from ..inspection import DaemonReadinessState
from ..services import ServiceDaemon
from ..spawning import MultiprocessingSpawning
from ..waiting import FnWait
from ..waiting import SequentialWait
from .testing import TEST_TIMEOUT_S
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import wait_pidfile_unlocked


##


def _python_cmd(*args: str) -> tuple[str, ...]:
    return (
        os.path.abspath('python'),
        '-m',
        'omcore.daemons.children.tests.helper',
        *args,
    )


def _reserve_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _stop_process(process) -> None:
    if process.is_alive():
        os.kill(process.pid, signal.SIGTERM)
        process.join(2.)
    if process.is_alive():
        process.kill()
        process.join(TEST_TIMEOUT_S)
    process.close()


##


def test_daemon_inspection_tracks_real_lifecycle_and_replacement_identity() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'supervisor.pid')
        event_file = os.path.join(temp_dir, 'events.jsonl')
        output_file = os.path.join(temp_dir, 'child.log')
        port = _reserve_port()

        wait = HttpWait(
            url=f'http://127.0.0.1:{port}/healthz',
            expected_body=b'healthy',
            timeout_s=.1,
        )
        daemon = ServiceDaemon(
            ChildProcessService.Config(
                process=ChildProcessConfig(
                    cmd=_python_cmd(
                        '--event-file', event_file,
                        '--port', str(port),
                        '--startup-delay-s', '.3',
                    ),
                    stdout=ChildProcessOutput.file(output_file),
                    stderr=ChildProcessOutput(mode=ChildProcessOutputMode.STDOUT),
                ),
                termination=ChildTerminationConfig(grace_timeout_s=2.),
            ),
            Daemon.Config(
                spawning=MultiprocessingSpawning(
                    start_method=MultiprocessingSpawning.StartMethod.SPAWN,
                ),
                pid_file=pid_file,
                wait=wait,
                wait_timeout=TEST_TIMEOUT_S,
                wait_sleep_s=.01,
            ),
        ).daemon_()

        assert daemon.inspect().state is DaemonLifecycleState.ABSENT

        processes = []
        try:
            assert daemon.launch_no_wait()
            starting = daemon.inspect()
            assert starting.state is DaemonLifecycleState.RUNNING
            assert starting.running
            assert not starting.ready
            assert starting.readiness is DaemonReadinessState.NOT_READY
            assert starting.pid is not None
            assert starting.info is not None
            assert starting.pid == starting.info.pid
            assert starting.pidfile_error is None
            assert starting.pidfile_inode is not None
            first_instance_id = starting.info.instance_id
            first_process = find_multiprocessing_child(starting.pid)
            processes.append(first_process)

            daemon.wait_sync()
            ready = daemon.inspect()
            assert ready.state is DaemonLifecycleState.READY
            assert ready.ready
            assert ready.readiness is DaemonReadinessState.READY
            assert ready.info == starting.info
            assert ready.pidfile_inode == starting.pidfile_inode

            def fail_readiness() -> bool:
                raise RuntimeError('inspection-readiness-failed')

            readiness_error = DaemonInspector(
                pid_file,
                wait=FnWait(fail_readiness),
            ).inspect()
            assert readiness_error.state is DaemonLifecycleState.RUNNING
            assert readiness_error.readiness is DaemonReadinessState.ERROR
            assert readiness_error.readiness_error == 'RuntimeError: inspection-readiness-failed'
            assert readiness_error.info == ready.info

            wait_calls: list[str] = []

            def first_wait() -> bool:
                wait_calls.append('first')
                return True

            def second_wait() -> bool:
                wait_calls.append('second')
                return False

            sequential_inspector = DaemonInspector(
                pid_file,
                wait=SequentialWait([
                    FnWait(first_wait),
                    FnWait(second_wait),
                ]),
            )
            assert sequential_inspector.inspect().readiness is DaemonReadinessState.NOT_READY
            assert sequential_inspector.inspect().readiness is DaemonReadinessState.NOT_READY
            assert wait_calls == ['first', 'second', 'first', 'second']

            os.kill(first_process.pid, signal.SIGTERM)
            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(first_process) == 0
            processes.remove(first_process)

            stale = daemon.inspect()
            assert stale.state is DaemonLifecycleState.STALE
            assert stale.exists
            assert not stale.running
            assert stale.readiness is DaemonReadinessState.NOT_CHECKED
            assert stale.info == ready.info
            assert stale.pidfile_inode == ready.pidfile_inode

            daemon.launch()
            replacement = daemon.inspect()
            assert replacement.state is DaemonLifecycleState.READY
            assert replacement.info is not None
            assert replacement.info.instance_id != first_instance_id
            assert replacement.pidfile_inode == stale.pidfile_inode
            replacement_process = find_multiprocessing_child(replacement.info.pid)
            processes.append(replacement_process)

            os.kill(replacement_process.pid, signal.SIGTERM)
            wait_pidfile_unlocked(pid_file)
            assert join_multiprocessing_child(replacement_process) == 0
            processes.remove(replacement_process)

        finally:
            for process in processes:
                _stop_process(process)


def test_daemon_inspection_reports_stale_legacy_and_malformed_records() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')

        with open(pid_file, 'w') as file:
            file.write('12345\n')

        legacy = DaemonInspector(pid_file).inspect()
        assert legacy.state is DaemonLifecycleState.STALE
        assert legacy.pid == 12345
        assert legacy.info is None
        assert legacy.pidfile_error is None

        with open(pid_file, 'w') as file:
            file.write('not-a-pid\n')

        malformed = DaemonInspector(pid_file).inspect()
        assert malformed.state is DaemonLifecycleState.STALE
        assert malformed.pid is None
        assert malformed.info is None
        assert malformed.pidfile_error == (
            "DaemonPidfileInfoError: Invalid daemon pid line: 'not-a-pid'"
        )
