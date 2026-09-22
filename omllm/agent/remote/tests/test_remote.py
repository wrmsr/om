import asyncio
import contextlib
import os
import pathlib
import shlex
import typing as ta

import pytest

from omcore.os.pyremote.core import PyremoteBootstrapDriver
from omcore.os.pyremote.core import pyremote_build_bootstrap_source

from ....core import processes
from ....core.rpc.channels import AsyncioStreamRpcChannel
from ...exec.ops import ExecParams
from ...exec.ops import ProcessesExecOps
from ...fs.ops import FsFileChangedError
from ..client import RemoteAgentClient
from ..payload import get_remote_agent_payload_src


##


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
_PYTHON_38_AVAILABLE = (_REPO_ROOT / '.venvs' / '8' / 'pyvenv.cfg').is_file()


@contextlib.asynccontextmanager
async def _remote_agent() -> ta.AsyncIterator[RemoteAgentClient]:
    env = dict(os.environ)
    if _PYTHON_38_AVAILABLE:
        env['VENV'] = '8'
    proc = await asyncio.create_subprocess_exec(
        str(_REPO_ROOT / 'python'),
        '-c',
        pyremote_build_bootstrap_source('omllm-agent-test'),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
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
