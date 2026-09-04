import asyncio
import time

import pytest

from ....core import processes
from ..ops import ExecParams
from ..ops import ProcessesExecOps
from ..ops import format_exec_output


@pytest.mark.asyncs('asyncio')
async def test_procs_exec_ops_basic(tmp_path):
    async with processes.AsyncioProcessManager() as m:
        ops = ProcessesExecOps()
        env = {'PATH': '/usr/bin:/bin', 'FOO': 'bar'}

        r = await ops.exec(m.root, ExecParams(
            ['sh', '-c', 'echo out $FOO; echo err >&2; exit 0'],
            cwd=str(tmp_path),
            env=env,
        ))
        assert r.rc == 0
        assert r.stdout == b'out bar\n'
        assert r.stderr == b'err\n'
        assert not r.timed_out
        assert not m.processes

        # nonzero exit
        r = await ops.exec(m.root, ExecParams(['sh', '-c', 'exit 7'], cwd=str(tmp_path), env=env))
        assert r.rc == 7

        # timeout -> killed, timed_out flag, partial output preserved
        r = await ops.exec(m.root, ExecParams(
            ['sh', '-c', 'echo before; sleep 10'],
            cwd=str(tmp_path),
            env=env,
            timeout_s=0.3,
        ))
        assert r.timed_out
        assert r.rc != 0
        assert b'before' in (r.stdout or b'')
        assert not m.processes


def test_format_exec_output():
    from ..ops import ExecResult

    assert format_exec_output(ExecResult(rc=0, stdout=b'hi\n')) == 'hi\n'

    # stderr appended after stdout
    out = format_exec_output(ExecResult(rc=0, stdout=b'a\n', stderr=b'b\n'))
    assert out == 'a\nb\n'

    # nonzero exit note
    out = format_exec_output(ExecResult(rc=2, stdout=b'x\n'))
    assert out.endswith('[exit code 2]')

    # timeout note
    out = format_exec_output(ExecResult(rc=-9, timed_out=True), timeout_s=5)
    assert 'timed out after 5s' in out

    # head+tail truncation
    body = ('A' * 50_000)
    out = format_exec_output(ExecResult(rc=0, stdout=body.encode()), max_chars=1000)
    assert 'characters of output truncated' in out
    assert len(out) < 1500

    assert format_exec_output(ExecResult(rc=0)) == '(no output)'


##


import dataclasses as _dc  # noqa: E402

from ....core import processes as _procs  # noqa: E402


@_dc.dataclass(frozen=True)
class _EchoSandbox(_procs.Sandbox):
    def transform_spec(self, spec):
        # observably wraps: echoes a marker to stderr, then execs the original command.
        return _dc.replace(spec, argv=['sh', '-c', 'echo SANDBOXED >&2; exec "$@"', 'sh', *spec.argv])


@pytest.mark.asyncs('asyncio')
async def test_procs_exec_ops_applies_options(tmp_path):
    async with processes.AsyncioProcessManager() as m:
        r = await ProcessesExecOps().exec(m.root, ExecParams(
            ['echo', 'hi'],
            cwd=str(tmp_path),
            env={'PATH': '/usr/bin:/bin'},
            options=(_EchoSandbox(),),
        ))
        assert r.rc == 0
        assert r.stdout == b'hi\n'
        assert r.stderr == b'SANDBOXED\n'


@pytest.mark.asyncs('asyncio')
async def test_cancelled_exec_returns_at_once_and_the_manager_finishes_the_process(tmp_path):
    spawned = asyncio.Event()
    reaped = asyncio.Event()

    def on_event(e):
        if isinstance(e, processes.ProcessSpawnedEvent):
            spawned.set()
        elif isinstance(e, processes.ProcessReapedEvent):
            reaped.set()

    async with processes.AsyncioProcessManager() as m:
        m.subscribe(on_event)
        task = asyncio.create_task(ProcessesExecOps().exec(m.root, ExecParams(
            ['sh', '-c', 'trap "" TERM; while :; do sleep 0.05; done'],
            cwd=str(tmp_path),
            env={'PATH': '/usr/bin:/bin'},
            options=(processes.TerminationPolicy(grace_s=.3),),
        )))
        await spawned.wait()
        [proc] = m.processes.values()

        # The cancel comes back well inside the grace the TERM-immune process is given, ...
        t0 = time.monotonic()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert time.monotonic() - t0 < .2
        assert proc.closing

        # ... and the manager sees the kill through.
        await reaped.wait()
        assert proc.state is processes.ProcessState.REAPED
        assert not m.processes
