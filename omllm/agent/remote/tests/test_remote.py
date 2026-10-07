"""
The remote agent end to end: the generated amalgam, bootstrapped into a separate interpreter (the Python 3.8 venv when
there is one) exactly as the docker connection does it, and driven through `RemoteAgentClient`.
"""
import asyncio
import contextlib
import fcntl
import os
import pathlib
import sys
import time
import typing as ta

import pytest

from omcore import dataclasses as dc
from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source

from ....core import processes
from ....core.processes.remote.tests.support import TERMINATION_PROCESS_SRC
from ....core.rpc.channels import AsyncioStreamRpcChannel
from ...exec.ops import ExecParams
from ...exec.ops import ProcessesExecOps
from ...fs.common import FsFileChangedError
from ...fs.common import fs_file_digest
from ...fs.remote.client import DEFAULT_REMOTE_FS_CHUNK_BYTES
from ..client import RemoteAgentClient
from ..payload import get_remote_agent_payload_src


##


# FIXME: wow
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_PYTHON_38 = _REPO_ROOT / '.venvs' / '8' / 'bin' / 'python'
_PYTHON = str(_PYTHON_38) if _PYTHON_38.is_file() else sys.executable


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

        # Content past a chunk crosses the real agent in pieces, in both directions.
        big = os.urandom(DEFAULT_REMOTE_FS_CHUNK_BYTES * 2 + 12345)
        big_path = os.path.join(root, 'big.bin')
        assert (await client.fs.write_file(big_path, big)).created
        big_read = await client.fs.read_file(big_path)
        assert big_read.data == big
        assert big_read.digest == fs_file_digest(big)

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


@dc.dataclass(frozen=True, kw_only=True)
class _DisconnectRun:
    pid: int
    state_at_disconnect: str
    teardown_s: float
    agent_stderr: str


async def _run_until_disconnect(
        argv: ta.Sequence[str],
        *,
        cwd: str,
        before_disconnect: ta.Callable[[], None] | None = None,
) -> _DisconnectRun:
    """Spawns `argv` through a real agent, waits for its 'ready', then drops the connection and waits the agent out."""

    agent_stderr: list[str] = []
    async with _remote_agent(stderr_sink=agent_stderr) as client:
        process = await client.processes.root.spawn(processes.ProcessSpec(list(argv), cwd=cwd))
        ready = await process.spool.poll(0, timeout=5.)
        assert ready.data(1) == b'ready'
        if before_disconnect is not None:
            before_disconnect()

        # Recorded for the failure message below: together these help explain a missing termination marker.
        state_at_disconnect = (
            f'{process.state.name}, returncode={process.returncode}, output_ended={process.output_ended}'
        )
        disconnected_at = time.monotonic()
        await client.peer.aclose()
        await client.wait_closed()

    return _DisconnectRun(
        pid=process.pid,
        state_at_disconnect=state_at_disconnect,
        teardown_s=time.monotonic() - disconnected_at,
        agent_stderr=''.join(agent_stderr),
    )


async def _assert_terminated_gracefully(run: _DisconnectRun, terminated_path: str) -> None:
    if not os.path.exists(terminated_path):
        pytest.fail(_describe_missing_termination(
            state_at_disconnect=run.state_at_disconnect,
            teardown_s=run.teardown_s,
            pid_after=await _describe_pid(run.pid),
            agent_stderr=run.agent_stderr,
        ))
    assert pathlib.Path(terminated_path).read_bytes() == b'terminated'

    # A clean shutdown reports only its per-process outcomes: any traceback on the agent's stderr is a bug.
    assert 'Traceback' not in run.agent_stderr, run.agent_stderr


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_disconnect_terminates_processes(tmp_path) -> None:
    root = os.path.realpath(tmp_path)
    terminated_path = os.path.join(root, 'terminated')

    run = await _run_until_disconnect([_PYTHON, '-c', TERMINATION_PROCESS_SRC, terminated_path], cwd=root)
    await _assert_terminated_gracefully(run, terminated_path)


def _lock_held(path: str) -> bool:
    """Whether any process still holds a flock on `path`."""

    fd = os.open(path, os.O_RDONLY)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


@pytest.mark.asyncs('asyncio')
async def test_remote_agent_disconnect_sweeps_the_process_group(tmp_path) -> None:
    # The leader gets its graceful TERM as above and exits, leaving behind a descendant that ignores TERM: only the
    # sweep's group SIGKILL, sent while the exited leader still holds the group id, can end it. Its end is observed
    # through the flock it shares with the leader, which is free only once every holder is gone - no pids involved,
    # so nothing is fooled by one being recycled.
    root = os.path.realpath(tmp_path)
    terminated_path = os.path.join(root, 'terminated')
    lock_path = os.path.join(root, 'group.lock')

    def check_lock_held() -> None:
        assert _lock_held(lock_path)

    run = await _run_until_disconnect(
        [_PYTHON, '-c', TERMINATION_PROCESS_SRC, terminated_path, lock_path],
        cwd=root,
        before_disconnect=check_lock_held,
    )
    await _assert_terminated_gracefully(run, terminated_path)

    # The SIGKILL is sent before the agent exits, but the descendant finishes dying on its own schedule.
    deadline = time.monotonic() + 10.
    while _lock_held(lock_path):
        assert time.monotonic() < deadline, f'a TERM-ignoring descendant survived the group sweep:\n{run.agent_stderr}'
        await asyncio.sleep(.01)


##


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
