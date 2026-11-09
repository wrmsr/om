import errno
import os
import queue
import signal
import sys
import threading

import pytest

from omcore.testing.fakedarwin import FakeDarwinProcessGroups

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


def test_exit_waits_racing_the_reap_all_report_it() -> None:
    # A wait the reap pulls the child out from under - possible, as both wait on the same zombie - answers from the
    # reap's result rather than failing to find the child.
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(cmd=('/bin/sh', '-c', 'exit 5')))
    results: queue.Queue = queue.Queue()
    ready = threading.Barrier(4)

    def wait_exited() -> None:
        ready.wait()
        try:
            results.put(process.wait_exited())
        except BaseException as exc:  # noqa
            results.put(exc)

    threads = [threading.Thread(target=wait_exited) for _ in range(3)]
    for thread in threads:
        thread.start()
    ready.wait()
    assert process.reap() == 5
    for thread in threads:
        thread.join()

    assert [results.get_nowait() for _ in threads] == [5, 5, 5]


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


def test_group_signal_to_an_exited_group_is_a_lookup_error_on_darwin() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sh', '-c', 'exit 0'),
        start_new_session=True,
    ))
    try:
        # Observed but not reaped, so the group is left holding nothing but its zombie leader.
        assert process.wait_exited() == 0

        with FakeDarwinProcessGroups():
            # The kernel behavior being handled: a group of nothing but zombies cannot be signaled at all.
            with pytest.raises(PermissionError):
                os.killpg(process.pid, 0)

            with pytest.raises(ProcessLookupError):
                process.send_signal(signal.SIGTERM, process_group=True)
            with pytest.raises(ProcessLookupError):
                process.kill(process_group=True)

            # Signaling the zombie itself succeeds, there as everywhere.
            process.send_signal(signal.SIGTERM)

    finally:
        process.reap()


@pytest.mark.skipif(sys.platform == 'darwin', reason='darwin refuses to signal a group of nothing but zombies')
def test_group_signal_to_an_exited_group_succeeds_elsewhere() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sh', '-c', 'exit 0'),
        start_new_session=True,
    ))
    try:
        assert process.wait_exited() == 0
        process.send_signal(signal.SIGTERM, process_group=True)
        process.kill(process_group=True)
        process.send_signal(signal.SIGTERM)
    finally:
        process.reap()


def test_group_signal_eperm_for_a_live_leader_is_raised() -> None:
    process = PopenChildProcessFactory().spawn(ChildProcessConfig(
        cmd=('/bin/sleep', '60'),
        start_new_session=True,
    ))
    try:
        def eperm(pid: int, sig: int) -> None:
            raise PermissionError(errno.EPERM, 'Operation not permitted')

        # A live leader we may not signal - one running setuid, say - cannot be arranged here, so EPERM is injected. As
        # on darwin, so that it is the liveness probe, not the platform, that decides to raise.
        with FakeDarwinProcessGroups(killpg=eperm):
            with pytest.raises(PermissionError):
                process.send_signal(signal.SIGTERM, process_group=True)

    finally:
        process.kill()
        process.reap()
