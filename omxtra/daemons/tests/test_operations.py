import concurrent.futures as cf
import os
import tempfile
import time

import pytest

from ..daemon import Daemon
from ..inspection import DaemonInspector
from ..inspection import DaemonLifecycleState
from ..operations import DaemonWaitStoppedReason
from ..operations import DaemonWaitStoppedTimeoutError
from ..operations import wait_daemon_stopped
from ..targets import FnTarget
from .testing import TEST_TIMEOUT_S
from .testing import PidfileHolder


##


def test_wait_daemon_stopped_observes_the_original_lock_release() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file) as holder:
            daemon = Daemon(
                FnTarget(lambda: None),
                Daemon.Config(
                    pid_file=pid_file,
                    wait_timeout=TEST_TIMEOUT_S,
                    wait_sleep_s=.01,
                ),
            )
            initial = daemon.inspect()
            assert initial.state is DaemonLifecycleState.RUNNING
            assert initial.info == holder.info

            with cf.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    daemon.wait_stopped,
                    initial=initial,
                )
                time.sleep(.05)
                assert not future.done()
                holder.close()
                result = future.result(TEST_TIMEOUT_S)

        assert result.reason is DaemonWaitStoppedReason.STOPPED
        assert result.stopped
        assert not result.replaced
        assert result.initial == initial
        assert result.final.state is DaemonLifecycleState.STALE
        assert result.final.info == initial.info


def test_wait_daemon_stopped_times_out_with_the_last_observation() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file):
            initial = DaemonInspector(pid_file).inspect()
            with pytest.raises(DaemonWaitStoppedTimeoutError) as exc_info:
                wait_daemon_stopped(
                    pid_file,
                    initial=initial,
                    timeout=.05,
                    sleep_s=.01,
                )

        assert exc_info.value.initial == initial
        assert exc_info.value.last.state is DaemonLifecycleState.RUNNING
        assert exc_info.value.last.pidfile_inode == initial.pidfile_inode


def test_wait_daemon_stopped_detects_path_inode_replacement() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file) as original:
            initial = DaemonInspector(pid_file).inspect()
            os.unlink(pid_file)

            with PidfileHolder(pid_file) as replacement:
                result = wait_daemon_stopped(
                    pid_file,
                    initial=initial,
                    timeout=TEST_TIMEOUT_S,
                )

                assert result.reason is DaemonWaitStoppedReason.REPLACED
                assert result.replaced
                assert not result.stopped
                assert result.final.state is DaemonLifecycleState.RUNNING
                assert result.final.pidfile_inode != initial.pidfile_inode
                assert result.final.info == replacement.info
                assert result.final.info != original.info


def test_wait_daemon_stopped_detects_uuid_replacement_on_the_same_inode() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file) as original:
            initial = DaemonInspector(pid_file).inspect()
            assert initial.info == original.info

        with PidfileHolder(pid_file) as replacement:
            current = DaemonInspector(pid_file).inspect()
            assert current.pidfile_inode == initial.pidfile_inode
            assert current.info == replacement.info

            result = wait_daemon_stopped(
                pid_file,
                initial=initial,
                timeout=TEST_TIMEOUT_S,
            )

        assert result.reason is DaemonWaitStoppedReason.REPLACED
        assert result.replaced
        assert result.final.info == replacement.info
        assert result.final.info != original.info


def test_wait_daemon_stopped_returns_immediately_without_an_owner() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        result = wait_daemon_stopped(pid_file)

        assert result.reason is DaemonWaitStoppedReason.ALREADY_STOPPED
        assert result.stopped
        assert result.initial.state is DaemonLifecycleState.ABSENT
        assert result.final == result.initial
