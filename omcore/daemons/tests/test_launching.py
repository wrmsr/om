import datetime
import json
import multiprocessing as mp
import os
import subprocess
import sys
import tempfile
import warnings

import pytest

from ..daemon import Daemon
from ..launching import Launcher
from ..spawning import ForkSpawning
from ..spawning import MultiprocessingSpawning
from ..spawning import ThreadSpawning
from ..startup import LaunchError
from .helpers import ControlledTarget
from .helpers import UnregisteredTarget
from .helpers import close_controlled_target_probe_fd
from .helpers import controlled_multiprocessing_entrypoint
from .helpers import failing_multiprocessing_entrypoint
from .testing import TEST_TIMEOUT_S
from .testing import accept_worker
from .testing import find_multiprocessing_child
from .testing import join_multiprocessing_child
from .testing import make_unix_listener
from .testing import read_locked_daemon_pidfile_info
from .testing import read_locked_pidfile
from .testing import receive_json_line
from .testing import release_worker
from .testing import wait_fork_child
from .testing import wait_pidfile_unlocked


##


def _make_spawning(kind):
    if kind == 'thread':
        return ThreadSpawning(linger=True)

    if kind == 'multiprocessing_spawn':
        return MultiprocessingSpawning(
            start_method=MultiprocessingSpawning.StartMethod.SPAWN,
            entrypoint=controlled_multiprocessing_entrypoint,
        )

    if kind == 'multiprocessing_fork':
        return MultiprocessingSpawning(
            start_method=MultiprocessingSpawning.StartMethod.FORK,
            entrypoint=controlled_multiprocessing_entrypoint,
        )

    if kind == 'fork':
        return ForkSpawning()

    raise ValueError(kind)


def _launch(launcher, kind):
    origin_pid = os.getpid()
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                'ignore',
                message='This process .* is multi-threaded.*',
                category=DeprecationWarning,
            )
            return launcher.launch()

    except SystemExit as exc:
        if kind == 'fork' and os.getpid() != origin_pid:
            os._exit(exc.code if isinstance(exc.code, int) else 1)
        raise


@pytest.mark.parametrize('kind', [
    'thread',
    'multiprocessing_spawn',
    'multiprocessing_fork',
    'fork',
])
def test_launcher_pidfile_single_instance_and_lifecycle(kind):
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'worker.pid')
        bootstrap_file = os.path.join(temp_dir, 'worker.log')

        spawning = _make_spawning(kind)
        target = ControlledTarget(
            control_path,
            label=kind,
            bootstrap_file=bootstrap_file if kind.startswith('multiprocessing_') else None,
        )

        conn = None
        process = None
        worker_pid = None
        exit_code = None

        with make_unix_listener(control_path) as listener:
            try:
                launcher = Launcher(
                    target=target,
                    spawning=spawning,
                    pid_file=pid_file,
                )
                assert _launch(launcher, kind)

                conn, info = accept_worker(listener)
                worker_pid = info['pid']

                if kind.startswith('multiprocessing_'):
                    process = find_multiprocessing_child(worker_pid)

                locked_pid = read_locked_pidfile(pid_file)
                pidfile_info = read_locked_daemon_pidfile_info(pid_file)
                second_launched = _launch(Launcher(
                    target=target,
                    spawning=spawning,
                    pid_file=pid_file,
                ), kind)

                bootstrap_log = ''
                if kind.startswith('multiprocessing_'):
                    with open(bootstrap_file) as f:
                        bootstrap_log = f.read()

            finally:
                if conn is not None:
                    release_worker(conn)
                if worker_pid is not None:
                    wait_pidfile_unlocked(pid_file)
                if process is not None:
                    exit_code = join_multiprocessing_child(process)
                elif kind == 'fork' and worker_pid is not None:
                    exit_code = wait_fork_child(worker_pid)

        assert locked_pid == worker_pid
        assert pidfile_info.pid == worker_pid
        assert pidfile_info.instance_id == info['instance_id']
        assert pidfile_info.started_at.utcoffset() == datetime.timedelta()
        assert not second_launched
        assert info['label'] == kind

        if kind == 'thread':
            assert worker_pid == os.getpid()
        else:
            assert worker_pid != os.getpid()
            assert info['ppid'] == os.getpid()

        if kind.startswith('multiprocessing_'):
            assert kind.removeprefix('multiprocessing_').upper() in bootstrap_log

        if exit_code is not None:
            assert exit_code == 0

        assert not Daemon(
            target,
            Daemon.Config(
                spawning=spawning,
                pid_file=pid_file,
            ),
        ).is_pidfile_locked()


@pytest.mark.parametrize('kind', [
    'multiprocessing_spawn',
    'fork',
])
def test_launcher_failure_releases_pidfile_and_child_exits_nonzero(kind):
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'worker.pid')

        process = None
        worker_pid = None

        with make_unix_listener(control_path) as listener:
            launcher = Launcher(
                target=ControlledTarget(control_path, fail=True),
                spawning=_make_spawning(kind),
                pid_file=pid_file,
            )
            assert _launch(launcher, kind)

            conn, info = accept_worker(listener)
            worker_pid = info['pid']
            if kind == 'multiprocessing_spawn':
                process = find_multiprocessing_child(worker_pid)

            release_worker(conn)
            wait_pidfile_unlocked(pid_file)

            if process is not None:
                exit_code = join_multiprocessing_child(process)
            else:
                exit_code = wait_fork_child(worker_pid)

        assert exit_code == 1


@pytest.mark.parametrize('kind', [
    'thread',
    'multiprocessing_spawn',
    'fork',
])
def test_startup_failure_is_reported_and_owned_child_is_reaped(kind):
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'worker.pid')

        with pytest.raises(LaunchError) as exc_info:
            _launch(Launcher(
                target=UnregisteredTarget(),
                spawning=_make_spawning(kind),
                pid_file=pid_file,
            ), kind)

        error = exc_info.value.info
        assert isinstance(error.pid, int)
        assert error.exception_type == 'builtins.TypeError'
        assert 'UnregisteredTarget' in error.message
        assert error.traceback is not None

        wait_pidfile_unlocked(pid_file)

        if kind == 'thread':
            assert error.pid == os.getpid()
        elif kind == 'fork':
            with pytest.raises(ChildProcessError):
                os.waitpid(error.pid, os.WNOHANG)
        else:
            assert all(process.pid != error.pid for process in mp.active_children())


def test_multiprocessing_entrypoint_startup_failure_is_reported():
    spawning = MultiprocessingSpawning(
        start_method=MultiprocessingSpawning.StartMethod.SPAWN,
        entrypoint=failing_multiprocessing_entrypoint,
    )

    with pytest.raises(LaunchError) as exc_info:
        Launcher(
            target=UnregisteredTarget(),
            spawning=spawning,
        ).launch()

    error = exc_info.value.info
    assert isinstance(error.pid, int)
    assert error.exception_type == 'builtins.RuntimeError'
    assert error.message == 'Entrypoint failed before target: SPAWN'
    assert all(process.pid != error.pid for process in mp.active_children())


def test_raw_fork_post_fork_hook_can_close_inherited_fd():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        read_fd, write_fd = os.pipe()

        try:
            with make_unix_listener(control_path) as listener:
                assert _launch(Launcher(
                    target=ControlledTarget(
                        control_path,
                        label='post-fork',
                        probe_fd=read_fd,
                    ),
                    spawning=ForkSpawning(
                        post_fork=close_controlled_target_probe_fd,
                    ),
                ), 'fork')

                conn, info = accept_worker(listener)
                worker_pid = info['pid']

                os.fstat(read_fd)
                release_worker(conn)
                assert wait_fork_child(worker_pid) == 0

                assert info['probe_fd_open'] is False

        finally:
            os.close(read_fd)
            os.close(write_fd)


def test_reparented_multiprocessing_worker_has_final_pidfile_identity():
    with tempfile.TemporaryDirectory() as temp_dir:
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'worker.pid')

        prior_child_pids = {process.pid for process in mp.active_children()}

        with make_unix_listener(control_path) as listener:
            assert Launcher(
                target=ControlledTarget(control_path, label='reparented'),
                spawning=MultiprocessingSpawning(
                    start_method=MultiprocessingSpawning.StartMethod.SPAWN,
                ),
                pid_file=pid_file,
                reparent_process=True,
            ).launch()

            conn, info = accept_worker(listener)
            worker_pid = info['pid']
            assert read_locked_pidfile(pid_file) == worker_pid
            assert info['ppid'] != os.getpid()
            assert info['sid'] != os.getsid(0)

            release_worker(conn)
            wait_pidfile_unlocked(pid_file)

        for process in mp.active_children():
            if process.pid not in prior_child_pids:
                assert join_multiprocessing_child(process) == 0


def test_concurrent_launcher_processes_start_one_detached_worker():
    num_contenders = 6

    with tempfile.TemporaryDirectory() as temp_dir:
        barrier_path = os.path.join(temp_dir, 'barrier.sock')
        control_path = os.path.join(temp_dir, 'control.sock')
        pid_file = os.path.join(temp_dir, 'worker.pid')

        processes = []
        barrier_connections = []
        worker_conn = None

        with make_unix_listener(barrier_path) as barrier_listener:
            with make_unix_listener(control_path) as control_listener:
                try:
                    for i in range(num_contenders):
                        processes.append(subprocess.Popen(
                            [
                                sys.executable,
                                '-m',
                                f'{__package__}.helpers',
                                'contend',
                                str(i),
                                barrier_path,
                                control_path,
                                pid_file,
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                        ))

                    ready_contenders = set()
                    for _ in range(num_contenders):
                        conn, _ = barrier_listener.accept()
                        conn.settimeout(TEST_TIMEOUT_S)
                        barrier_connections.append(conn)
                        ready_contenders.add(receive_json_line(conn)['contender'])

                    assert ready_contenders == {str(i) for i in range(num_contenders)}

                    for conn in barrier_connections:
                        conn.sendall(b'X')
                        conn.close()
                    barrier_connections.clear()

                    worker_conn, worker_info = accept_worker(control_listener)

                    results = []
                    for process in processes:
                        stdout, stderr = process.communicate(timeout=TEST_TIMEOUT_S)
                        assert process.returncode == 0, stderr
                        results.append(json.loads(stdout))

                    assert sum(result['launched'] for result in results) == 1
                    assert {result['contender'] for result in results} == {
                        str(i)
                        for i in range(num_contenders)
                    }
                    assert worker_info['label'] == 'detached'
                    assert read_locked_pidfile(pid_file) == worker_info['pid']

                finally:
                    for conn in barrier_connections:
                        conn.close()
                    if worker_conn is not None:
                        release_worker(worker_conn)
                    for process in processes:
                        if process.poll() is None:
                            process.terminate()
                            process.communicate(timeout=TEST_TIMEOUT_S)

                wait_pidfile_unlocked(pid_file)
