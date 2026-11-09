import errno
import os
import signal
import sys

import pytest

from ..configs import ChildProcessConfig
from ..processes import PopenChildProcessFactory


##


def test_group_signal_to_an_exited_group_is_a_lookup_error() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sh', '-c', 'exit 0'),
        start_new_session=True,
    ))
    try:
        # Observed but not reaped, so the group is left holding nothing but its zombie leader.
        os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOWAIT)

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

    finally:
        process.wait()


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
        process.wait()
