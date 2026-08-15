import os
import signal
import tempfile

import pytest

from ...os.pidfiles.pinning import PidfilePinner
from ...os.pidfiles.pinning import UnverifiedPidfilePinner
from ..daemon import Daemon
from ..inspection import DaemonInspector
from ..inspection import DaemonLifecycleState
from ..operations import DaemonWaitStoppedReason
from ..stopping import DaemonStopSafety
from ..stopping import DaemonStopTimeoutError
from ..stopping import DaemonStopUnavailableError
from ..stopping import stop_daemon
from ..targets import FnTarget
from .testing import TEST_TIMEOUT_S
from .testing import PidfileHolder


##


def test_daemon_stop_signals_a_verified_owner() -> None:
    if PidfilePinner.default_impl() is UnverifiedPidfilePinner:
        pytest.skip('No verified pidfile-owner pinner is available')

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
            result = daemon.stop(initial=initial)

        assert result.pid == holder.info.pid
        assert result.signal == signal.SIGTERM
        assert result.signal_sent
        assert result.stopped
        assert not result.replaced
        assert result.wait_result.reason is DaemonWaitStoppedReason.STOPPED
        assert result.wait_result.initial == initial
        assert result.wait_result.final.state is DaemonLifecycleState.STALE


def test_stop_daemon_fails_closed_with_an_unverified_pinner() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file) as holder:
            initial = DaemonInspector(pid_file).inspect()

            with pytest.raises(DaemonStopUnavailableError):
                stop_daemon(
                    pid_file,
                    initial=initial,
                    pinner=UnverifiedPidfilePinner(sleep_s=.01),
                )

            assert holder.is_alive()
            assert DaemonInspector(pid_file).inspect().info == holder.info


def test_stop_daemon_permits_explicit_unverified_pid_signaling() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file) as holder:
            initial = DaemonInspector(pid_file).inspect()
            result = stop_daemon(
                pid_file,
                initial=initial,
                timeout=TEST_TIMEOUT_S,
                pinner=UnverifiedPidfilePinner(sleep_s=.01),
                safety=DaemonStopSafety.ALLOW_UNVERIFIED,
                sleep_s=.01,
            )

        assert result.pid == holder.info.pid
        assert result.signal_sent
        assert result.wait_result.reason is DaemonWaitStoppedReason.STOPPED


def test_stop_daemon_does_not_signal_a_replacement_instance() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file) as original:
            initial = DaemonInspector(pid_file).inspect()

        with PidfileHolder(pid_file) as replacement:
            result = stop_daemon(
                pid_file,
                initial=initial,
                timeout=TEST_TIMEOUT_S,
                pinner=UnverifiedPidfilePinner(sleep_s=.01),
                safety=DaemonStopSafety.ALLOW_UNVERIFIED,
                sleep_s=.01,
            )

            assert result.pid is None
            assert not result.signal_sent
            assert result.replaced
            assert result.wait_result.reason is DaemonWaitStoppedReason.REPLACED
            holder_info = replacement.info
            assert result.wait_result.final.info == holder_info
            assert holder_info != original.info
            assert replacement.is_alive()


def test_stop_daemon_returns_already_stopped_without_selecting_a_pinner() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        result = stop_daemon(pid_file)

        assert result.pid is None
        assert not result.signal_sent
        assert result.stopped
        assert result.wait_result.reason is DaemonWaitStoppedReason.ALREADY_STOPPED


def test_stop_daemon_does_not_escalate_after_timeout() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        pid_file = os.path.join(temp_dir, 'service.pid')
        with PidfileHolder(pid_file, ignored_signals=(signal.SIGTERM,)) as holder:
            initial = DaemonInspector(pid_file).inspect()

            with pytest.raises(DaemonStopTimeoutError) as exc_info:
                stop_daemon(
                    pid_file,
                    initial=initial,
                    timeout=.05,
                    pinner=UnverifiedPidfilePinner(sleep_s=.01),
                    safety=DaemonStopSafety.ALLOW_UNVERIFIED,
                    sleep_s=.01,
                )

            assert exc_info.value.initial == initial
            assert exc_info.value.last.state is DaemonLifecycleState.RUNNING
            assert exc_info.value.pid == holder.info.pid
            assert exc_info.value.signal == signal.SIGTERM
            assert exc_info.value.signal_sent
            assert holder.is_alive()
