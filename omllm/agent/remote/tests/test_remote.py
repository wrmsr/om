import asyncio
import contextlib
import ctypes
import os
import pathlib
import signal
import sys
import time
import types
import typing as ta

import pytest

from omcore.lite.marshal import unmarshal_obj
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
from ..protocol import PROCESS_OUTPUT_METHOD
from ..protocol import OutputEvent


##


# FIXME: wow
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_PYTHON_38 = _REPO_ROOT / '.venvs' / '8' / 'bin' / 'python'
_PYTHON = str(_PYTHON_38) if _PYTHON_38.is_file() else sys.executable


# Darwin's Bash 3.2 can defer a TERM trap around `sleep & wait` until the sleep finishes, or even crash. Either leaves
# the termination marker missing even when killpg succeeds. Use a single Python process to avoid that shell
# fork/wait race, and keep the helper compatible with the Python 3.8 interpreter used for the remote agent.
_TERMINATION_PROCESS_SRC = """
import os
import signal
import sys


def _main():
    # Block TERM before announcing readiness: sigwait consumes it even if it arrives before the wait starts.
    # Python handlers are deferred, so signal.signal + signal.pause would leave a smaller lost-wakeup window.
    term_signals = {signal.SIGTERM}
    signal.pthread_sigmask(signal.SIG_BLOCK, term_signals)
    os.write(1, b'ready')
    signal.sigwait(term_signals)
    with open(sys.argv[1], 'wb') as f:
        f.write(b'terminated')


if __name__ == '__main__':
    _main()
"""


@contextlib.asynccontextmanager
async def _remote_agent(*, stderr_sink: list[str] | None = None) -> ta.AsyncIterator[RemoteAgentClient]:
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
        if stderr_sink is not None:
            stderr_sink.append(stderr)
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
async def test_remote_close_reprobes_a_stale_exit_belief_before_killing(tmp_path) -> None:
    # A stale "already exited" belief must not make close skip the graceful signal: a live process still gets its TERM,
    # and the chance to write its marker, before any KILL. Driven in process, with the belief injected directly.
    stdout = asyncio.StreamReader()

    class ProcessService(remote_server._RemoteProcessService):  # noqa: SLF001
        async def notify(self, method: str, params: ta.Any) -> None:
            if method == PROCESS_OUTPUT_METHOD:
                event: OutputEvent = unmarshal_obj(params, OutputEvent)
                if event.fd == 1:
                    stdout.feed_data(event.data)
            await super().notify(method, params)

    service = ProcessService()
    service._ensure_sigchld()  # noqa: SLF001
    terminated_path = os.path.join(os.path.realpath(tmp_path), 'terminated')
    try:
        spawned = await service.spawn({
            'argv': [_PYTHON, '-c', _TERMINATION_PROCESS_SRC, terminated_path],
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


async def _describe_pid(pid: int) -> str:
    """How a pid looks from here, for diagnostics. Only ever inspected, never signaled: it may have been recycled."""

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return 'gone'
    except PermissionError:
        pass
    try:
        ps = await asyncio.create_subprocess_exec(
            'ps', '-ww', '-o', 'pid=,ppid=,pgid=,stat=,args=', '-p', str(pid),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await asyncio.wait_for(ps.communicate(), 10.)
    except (OSError, TimeoutError) as e:
        return f'ALIVE (ps unavailable: {e!r})'
    return f'ALIVE: {out.decode("utf-8", "replace").strip()}'


def _describe_missing_termination(
        *,
        state_at_disconnect: str,
        teardown_s: float,
        pid_after: str,
        agent_stderr: str,
) -> str:
    return '\n'.join([
        'terminated file was not written (the child did not complete its TERM shutdown). A healthy run looks like:',
        'RUNNING at disconnect, teardown ~0.02s, child gone after, agent stderr "closed in ... returncode=0".',
        f'  child at disconnect:       {state_at_disconnect}   (EXITED here: it died on its own first)',
        f'  teardown after disconnect: {teardown_s:.3f}s   (> 5s: the graceful wait timed out, then SIGKILL)',
        f'  child pid after agent:     {pid_after}   (ALIVE: orphaned - its close failed or never ran)',
        '  agent stderr (returncode -9: SIGKILLed first; -15: killed by TERM; other negatives: died of that signal):',
        *[f'    {line}' for line in agent_stderr.splitlines() or ['<empty>']],
    ])


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_disconnect_terminates_processes(tmp_path) -> None:
    terminated_path = os.path.join(os.path.realpath(tmp_path), 'terminated')
    agent_stderr: list[str] = []

    async with _remote_agent(stderr_sink=agent_stderr) as client:
        process = await client.processes.root.spawn(processes.ProcessSpec(
            [_PYTHON, '-c', _TERMINATION_PROCESS_SRC, terminated_path],
            cwd=os.path.realpath(tmp_path),
        ))
        ready = await process.spool.poll(0, timeout=5.)
        assert ready.data(1) == b'ready'

        # Recorded for the failure message below: together these help explain a missing termination marker.
        state_at_disconnect = (
            f'{process.state.name}, returncode={process.returncode}, output_ended={process.output_ended}'
        )
        disconnected_at = time.monotonic()
        await client.peer.aclose()
        await client.wait_closed()

    teardown_s = time.monotonic() - disconnected_at

    if not os.path.exists(terminated_path):
        pytest.fail(_describe_missing_termination(
            state_at_disconnect=state_at_disconnect,
            teardown_s=teardown_s,
            pid_after=await _describe_pid(process.pid),
            agent_stderr=''.join(agent_stderr),
        ))
    assert pathlib.Path(terminated_path).read_bytes() == b'terminated'


##


@pytest.mark.asyncs('asyncio')
async def test_remote_shutdown_kills_a_process_whose_close_fails(capsys) -> None:
    service = remote_server._RemoteProcessService()  # noqa: SLF001
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
