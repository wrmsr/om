"""The target-side process service, driven in process: exit observation, signaling, close, and shutdown."""
import asyncio
import ctypes
import os
import pathlib
import signal
import sys
import types
import typing as ta

import pytest

from omcore.lite.marshal import unmarshal_obj

from .. import server as remote_server
from ..protocol import REMOTE_PROCESS_OUTPUT_METHOD
from ..protocol import RemoteProcessOutputEvent
from ..server import RemoteProcessService
from .support import TERMINATION_PROCESS_SRC


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
async def test_remote_close_reprobes_a_stale_exit_belief_before_killing(tmp_path) -> None:
    # A stale "already exited" belief must not make close skip the graceful signal: a live process still gets its TERM,
    # and the chance to write its marker, before any KILL. Driven in process, with the belief injected directly.
    stdout = asyncio.StreamReader()

    class ProcessService(RemoteProcessService):  # noqa: SLF001
        async def notify(self, method: str, params: ta.Any) -> None:
            if method == REMOTE_PROCESS_OUTPUT_METHOD:
                event: RemoteProcessOutputEvent = unmarshal_obj(params, RemoteProcessOutputEvent)
                if event.fd == 1:
                    stdout.feed_data(event.data)
            await super().notify(method, params)

    service = ProcessService()
    service._ensure_sigchld()  # noqa: SLF001
    terminated_path = os.path.join(os.path.realpath(tmp_path), 'terminated')
    try:
        spawned = await service.spawn({
            'argv': [sys.executable, '-c', TERMINATION_PROCESS_SRC, terminated_path],
            'cwd': os.path.realpath(tmp_path),
            'env': None,
            'name': None,
            'stdio': {'kind': 'pipes', 'stdin': 'devnull', 'stdout': 'pipe', 'stderr': 'pipe'},
        })
        process = service._processes[spawned['id']]  # noqa: SLF001
        # Synchronize with signal setup instead of assuming the child has started after a fixed delay.
        assert await asyncio.wait_for(stdout.readexactly(len(b'ready')), 5.) == b'ready'
        assert not process._exited.is_set()  # noqa: SLF001  # it is actually running

        # Inject the stale belief while the process is known to be alive.
        process._returncode = 0  # noqa: SLF001
        process._exited.set()  # noqa: SLF001

        result = await service.close({
            'id': spawned['id'],
            'policy': {
                'signal': int(signal.SIGTERM),
                'grace_s': 1.5,
                'kill_s': 1.5,
                'close_stdin': True,
                'process_group': True,
                # No drain window, so only the graceful signal-and-wait (reached by re-probing the stale belief) can
                # let it write its marker - the sweep would otherwise SIGKILL the group right after its SIGTERM.
                'drain_s': 0.,
            },
        })
        assert result['state'] == 'reaped'
        assert pathlib.Path(terminated_path).read_bytes() == b'terminated'
    finally:
        await service.aclose()


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


def test_remote_signal_group_eperm_falls_back_to_leader_pid(monkeypatch) -> None:
    # A killpg that reports EPERM (which macOS/BSD can do) must not swallow the signal: it is delivered to the owned
    # leader pid directly, so a live leader still gets its TERM (and runs its handlers).
    proc = _bare_server_process(4321)
    killed: list[tuple[int, int]] = []

    def fake_killpg(pid: int, sig: int) -> None:
        raise PermissionError

    monkeypatch.setattr(remote_server.os, 'killpg', fake_killpg)
    monkeypatch.setattr(remote_server.os, 'kill', lambda pid, sig: killed.append((pid, sig)))

    proc._signal(signal.SIGTERM, True)  # noqa: SLF001
    assert killed == [(4321, signal.SIGTERM)]


def test_remote_signal_group_success_does_not_also_hit_the_pid(monkeypatch) -> None:
    proc = _bare_server_process(4321)
    group_signals: list[tuple[int, int]] = []
    pid_signals: list[tuple[int, int]] = []

    monkeypatch.setattr(remote_server.os, 'killpg', lambda pid, sig: group_signals.append((pid, sig)))
    monkeypatch.setattr(remote_server.os, 'kill', lambda pid, sig: pid_signals.append((pid, sig)))

    proc._signal(signal.SIGTERM, True)  # noqa: SLF001
    assert group_signals == [(4321, signal.SIGTERM)]
    assert pid_signals == []
