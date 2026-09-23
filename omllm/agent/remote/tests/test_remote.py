import asyncio
import contextlib
import ctypes
import os
import pathlib
import shlex
import sys
import typing as ta

import pytest

from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source

from ....core import processes
from ....core.rpc.channels import AsyncioStreamRpcChannel
from ...exec.ops import ExecParams
from ...exec.ops import ProcessesExecOps
from ...fs.ops import FsFileChangedError
from .. import server as remote_server
from ..client import RemoteAgentClient
from ..payload import get_remote_agent_payload_src


##


# FIXME: wow
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_PYTHON_38 = _REPO_ROOT / '.venvs' / '8' / 'bin' / 'python'
_PYTHON = str(_PYTHON_38) if _PYTHON_38.is_file() else sys.executable


@contextlib.asynccontextmanager
async def _remote_agent() -> ta.AsyncIterator[RemoteAgentClient]:
    proc = await asyncio.create_subprocess_exec(
        _PYTHON,
        '-c',
        pyremote_build_bootstrap_source('omllm-agent-test'),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    assert proc.stderr is not None

    client: RemoteAgentClient | None = None
    try:
        await PyremoteBootstrapDriver([
            get_remote_agent_payload_src(),
            'remote_agent_main()',
        ]).async_run(proc.stdout, proc.stdin)

        client = RemoteAgentClient(AsyncioStreamRpcChannel(proc.stdout, proc.stdin))
        await client.start()
        yield client

    finally:
        if client is not None:
            await client.aclose()
        elif proc.stdin.can_write_eof():
            proc.stdin.write_eof()
        else:
            proc.stdin.close()

        try:
            returncode = await asyncio.wait_for(proc.wait(), 10.)
        except TimeoutError:
            proc.kill()
            returncode = await proc.wait()
        stderr = (await proc.stderr.read()).decode('utf-8', 'replace')
        assert returncode == 0, stderr


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


##


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_amalg_files_processes_and_pty(tmp_path) -> None:
    async with _remote_agent() as client:
        root = os.path.realpath(tmp_path)
        path = os.path.join(root, 'file.txt')

        created = await client.fs.write_file(path, b'one')
        assert created.created
        first = await client.fs.read_file(path)
        assert first.data == b'one'
        assert (await client.fs.stat(path)).is_file

        await client.fs.write_file(path, b'two', overwrite=True, expected_digest=first.digest)
        with pytest.raises(FsFileChangedError):
            await client.fs.write_file(path, b'three', overwrite=True, expected_digest=first.digest)

        globbed = await client.fs.glob(os.path.join(root, '*.txt'), root=root)
        assert [entry.path for entry in globbed.entries] == [path]

        result = await ProcessesExecOps().exec(client.processes.root, ExecParams(
            ['sh', '-c', 'printf stdout; printf stderr >&2; exit 7'],
            cwd=root,
        ))
        assert result.rc == 7
        assert result.stdout == b'stdout'
        assert result.stderr == b'stderr'

        timed_out = await ProcessesExecOps().exec(client.processes.root, ExecParams(
            ['sh', '-c', 'printf before-timeout; exec sleep 30'],
            cwd=root,
            timeout_s=.05,
        ))
        assert timed_out.timed_out
        assert timed_out.stdout == b'before-timeout'

        interactive = await client.processes.root.spawn(processes.ProcessSpec(
            ['sh', '-c', 'read line; printf "out:%s\\n" "$line"; printf "err:%s\\n" "$line" >&2'],
            cwd=root,
            stdio=processes.ProcessStdio(stdin='pipe', stdout='pipe', stderr='pipe'),
        ))
        await interactive.write(b'hello\n')
        await interactive.write_eof()
        assert await interactive.wait(5.) == 0
        await interactive.aclose()
        interactive_output = interactive.spool.read_available().data()
        assert b'out:hello\n' in interactive_output
        assert b'err:hello\n' in interactive_output
        interactive.spool.close()

        pty_process = await client.processes.root.spawn(processes.ProcessSpec(
            [
                'sh',
                '-c',
                'test -t 0 && test -t 1 && test -t 2 && printf "tty\\n"; read line; printf "got:%s\\n" "$line"',
            ],
            cwd=root,
            stdio=processes.PtyStdio(rows=20, cols=70),
        ))
        assert pty_process.has_pty
        assert pty_process.get_winsize() == (20, 70)
        await pty_process.resize(30, 100)
        assert pty_process.get_winsize() == (30, 100)
        await pty_process.write(b'world\n')
        assert await pty_process.wait(5.) == 0
        await pty_process.aclose()
        pty_output = pty_process.spool.read_available().data()
        assert b'tty' in pty_output
        assert b'got:world' in pty_output
        pty_process.spool.close()

        assert not client.processes.root.processes


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_disconnect_terminates_processes(tmp_path) -> None:
    terminated_path = os.path.join(os.path.realpath(tmp_path), 'terminated')
    trap_command = f'printf terminated > {shlex.quote(terminated_path)}; exit 0'

    async with _remote_agent() as client:
        process = await client.processes.root.spawn(processes.ProcessSpec(
            [
                'sh',
                '-c',
                f'trap {shlex.quote(trap_command)} TERM; printf ready; while :; do sleep 30; done',
            ],
            cwd=os.path.realpath(tmp_path),
        ))
        ready = await process.spool.poll(0, timeout=5.)
        assert ready.data(1) == b'ready'

        await client.peer.aclose()
        await client.wait_closed()

    assert pathlib.Path(terminated_path).read_bytes() == b'terminated'


##


def test_remote_waitstatus_to_exitcode() -> None:
    for status in (0, 7 << 8, 255 << 8, 9, 15, 0x80 | 6):
        assert remote_server._remote_waitstatus_to_exitcode(status) == os.waitstatus_to_exitcode(status)  # noqa: SLF001


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_observes_exits_with_many_live_processes() -> None:
    # Exit observation must not cost a thread per child: with more live children than the default executor has threads,
    # a later child's exit would otherwise go unnoticed until one of the earlier ones died.
    async with _remote_agent() as client:
        n = min(32, (os.cpu_count() or 1) + 4)
        sleepers = [
            await client.processes.root.spawn(processes.ProcessSpec(['sleep', '60']))
            for _ in range(n)
        ]
        quick = await client.processes.root.spawn(processes.ProcessSpec(['true']))
        assert await quick.wait(10.) == 0
        await quick.aclose()
        assert quick.state is processes.ProcessState.REAPED
        assert len(client.processes.processes) == len(sleepers)


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_events_are_ordered() -> None:
    async with _remote_agent() as client:
        delivered: list[str] = []

        async def on_event(event):
            if isinstance(event, processes.ProcessExitedEvent):
                await asyncio.sleep(.02)
            delivered.append(type(event).__name__)

        client.processes.subscribe(on_event)
        process = await client.processes.root.spawn(processes.ProcessSpec(['true']))
        assert await process.wait(5.) == 0
        await process.aclose()
        for _ in range(500):
            if len([n for n in delivered if n.startswith('Process')]) >= 3:
                break
            await asyncio.sleep(.01)
        assert [n for n in delivered if n.startswith('Process')] == [
            'ProcessSpawnedEvent',
            'ProcessExitedEvent',
            'ProcessReapedEvent',
        ]
