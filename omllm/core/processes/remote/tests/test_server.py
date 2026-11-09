"""The target-side process service, driven in process: exit observation, signaling, close, and shutdown."""
import asyncio
import ctypes
import os
import signal
import subprocess
import sys
import types
import typing as ta

import pytest

from .. import server as remote_server
from ..server import RemoteProcessService


##


def test_remote_process_wait_darwin_fallback(monkeypatch) -> None:
    calls: list[tuple[int, bool]] = []

    def fallback(pid: int, *, nohang: bool = False) -> int:
        calls.append((pid, nohang))
        return 7

    monkeypatch.delattr(remote_server.os, 'waitid')
    monkeypatch.setattr(remote_server.sys, 'platform', 'darwin')
    monkeypatch.setattr(remote_server, '_remote_darwin_process_wait', fallback)

    assert remote_server._remote_process_wait(123, nohang=True) == 7  # noqa: SLF001
    assert calls == [(123, True)]


def test_remote_darwin_process_wait_libc(monkeypatch) -> None:
    calls: list[tuple[int, int, int]] = []

    class FakeWaitid:
        argtypes: ta.Any = None
        restype: ta.Any = None
        exited = True

        def __call__(self, idtype: int, pid: int, info: ta.Any, options: int) -> int:
            calls.append((idtype, pid, options))
            if self.exited:
                info._obj.si_pid = pid  # noqa: SLF001
                info._obj.si_code = remote_server._REMOTE_CLD_KILLED  # noqa: SLF001
                info._obj.si_status = 9  # noqa: SLF001
            return 0

    fake_waitid = FakeWaitid()

    class FakeLibc:
        waitid = fake_waitid

    monkeypatch.setattr(ctypes, 'CDLL', lambda *_args, **_kwargs: FakeLibc())

    assert remote_server._remote_darwin_process_wait(456) == -9  # noqa: SLF001
    fake_waitid.exited = False
    assert remote_server._remote_darwin_process_wait(456, nohang=True) is None  # noqa: SLF001
    assert calls == [
        (
            remote_server._REMOTE_DARWIN_P_PID,  # noqa: SLF001
            456,
            remote_server._REMOTE_DARWIN_WEXITED | remote_server._REMOTE_DARWIN_WNOWAIT,  # noqa: SLF001
        ),
        (
            remote_server._REMOTE_DARWIN_P_PID,  # noqa: SLF001
            456,
            remote_server._REMOTE_DARWIN_WEXITED | remote_server._REMOTE_DARWIN_WNOWAIT | os.WNOHANG,  # noqa: SLF001
        ),
    ]


@pytest.mark.asyncs('asyncio')
async def test_remote_shutdown_kills_a_process_whose_close_fails(capsys) -> None:
    service = RemoteProcessService()  # noqa: SLF001
    spawned = await service.spawn({
        'argv': ['sleep', '30'],
        'cwd': None,
        'env': None,
        'name': None,
        'stdio': {'kind': 'pipes', 'stdin': 'devnull', 'stdout': 'pipe', 'stderr': 'pipe'},
    })
    process: ta.Any = service._processes[spawned['id']]  # noqa: SLF001

    async def failing_close(policy):
        raise RuntimeError('simulated close failure')

    process.close = failing_close
    await service.aclose()

    assert process._reaped  # noqa: SLF001
    assert process.returncode == -signal.SIGKILL
    assert not service._processes  # noqa: SLF001
    err = capsys.readouterr().err
    assert 'close failed' in err
    assert 'simulated close failure' in err
    assert f'killed, returncode={-signal.SIGKILL}' in err


def test_remote_waitstatus_to_exitcode() -> None:
    for status in (0, 7 << 8, 255 << 8, 9, 15, 0x80 | 6):
        assert remote_server._remote_waitstatus_to_exitcode(status) == os.waitstatus_to_exitcode(status)  # noqa: SLF001


def _bare_server_process(pid: int) -> ta.Any:
    proc: ta.Any = remote_server._RemoteServerProcess.__new__(remote_server._RemoteServerProcess)  # noqa: SLF001
    proc._reaped = False  # noqa: SLF001
    proc._exited = asyncio.Event()  # noqa: SLF001
    proc.popen = types.SimpleNamespace(pid=pid)
    return proc


def test_remote_signal_group_to_an_exited_leader_is_tolerated() -> None:
    # Observed but not reaped, the leader leaves its group holding nothing but a zombie, which darwin refuses to signal
    # with EPERM rather than ESRCH. The real kernel is used, so that is what this exercises there.
    popen = subprocess.Popen(['sh', '-c', 'exit 0'], start_new_session=True)
    try:
        os.waitid(os.P_PID, popen.pid, os.WEXITED | os.WNOWAIT)
        if sys.platform == 'darwin':
            with pytest.raises(PermissionError):
                os.killpg(popen.pid, 0)

        proc = _bare_server_process(popen.pid)
        proc._signal(signal.SIGTERM, True)  # noqa: SLF001
        proc._signal(signal.SIGKILL, True)  # noqa: SLF001
    finally:
        popen.wait()


def test_remote_signal_group_eperm_for_a_live_leader_is_raised(monkeypatch) -> None:
    # EPERM for a leader still alive - one we may not signal, being setuid say - is genuine and is raised. That cannot
    # be arranged here, so it is injected.
    popen = subprocess.Popen(['sleep', '60'], start_new_session=True)
    try:
        proc = _bare_server_process(popen.pid)

        def fake_killpg(pid: int, sig: int) -> None:
            raise PermissionError

        monkeypatch.setattr(remote_server.os, 'killpg', fake_killpg)
        with pytest.raises(PermissionError):
            proc._signal(signal.SIGTERM, True)  # noqa: SLF001
    finally:
        monkeypatch.undo()
        popen.kill()
        popen.wait()


def test_remote_signal_group_success_does_not_also_hit_the_pid(monkeypatch) -> None:
    proc = _bare_server_process(4321)
    group_signals: list[tuple[int, int]] = []
    pid_signals: list[tuple[int, int]] = []

    monkeypatch.setattr(remote_server.os, 'killpg', lambda pid, sig: group_signals.append((pid, sig)))
    monkeypatch.setattr(remote_server.os, 'kill', lambda pid, sig: pid_signals.append((pid, sig)))

    proc._signal(signal.SIGTERM, True)  # noqa: SLF001
    assert group_signals == [(4321, signal.SIGTERM)]
    assert pid_signals == []
