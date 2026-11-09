import errno
import os
import signal
import sys

import pytest

from ..configs import ChildProcessConfig
from ..processes import PopenChildProcessFactory


##


def test_exit_is_observed_without_reaping() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(cmd=('/bin/sh', '-c', 'exit 3')))
    assert process.wait_exited() == 3
    assert process.wait_exited() == 3

    # Still a zombie, and still ours to reap.
    result = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    assert result is not None
    assert result.si_pid == process.pid

    assert process.reap() == 3
    assert process.wait_exited() == 3
    with pytest.raises(ChildProcessError):
        os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)


def test_signals_after_reaping_are_lookup_errors() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sh', '-c', 'exit 0'),
        start_new_session=True,
    ))
    assert process.reap() == 0

    # Released, its pid may already name something else: nothing is sent.
    for process_group in (False, True):
        with pytest.raises(ProcessLookupError):
            process.send_signal(signal.SIGTERM, process_group=process_group)
        with pytest.raises(ProcessLookupError):
            process.kill(process_group=process_group)


def test_group_signal_to_an_exited_group_is_a_lookup_error() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sh', '-c', 'exit 0'),
        start_new_session=True,
    ))
    try:
        # Observed but not reaped, so the group is left holding nothing but its zombie leader.
        assert process.wait_exited() == 0

        if sys.platform == 'darwin':
            # The kernel behavior being handled: a group of nothing but zombies cannot be signaled at all.
            with pytest.raises(PermissionError):
                os.killpg(process.pid, 0)

            with pytest.raises(ProcessLookupError):
                process.send_signal(signal.SIGTERM, process_group=True)
            with pytest.raises(ProcessLookupError):
                process.kill(process_group=True)

        else:
            # Elsewhere signaling a group of zombies simply succeeds.
            process.send_signal(signal.SIGTERM, process_group=True)
            process.kill(process_group=True)

        # As does signaling the zombie itself, everywhere.
        process.send_signal(signal.SIGTERM)

    finally:
        process.reap()


def test_group_signal_eperm_for_a_live_leader_is_raised(monkeypatch) -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sleep', '60'),
        start_new_session=True,
    ))
    try:
        def eperm(pid, sig):
            raise PermissionError(errno.EPERM, 'Operation not permitted')

        # A live leader we may not signal - one running setuid, say - cannot be arranged here, so EPERM is injected.
        monkeypatch.setattr(os, 'killpg', eperm)
        with pytest.raises(PermissionError):
            process.send_signal(signal.SIGTERM, process_group=True)

    finally:
        monkeypatch.undo()
        process.kill()
        process.reap()
