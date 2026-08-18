import pytest

from ....core import procs
from ..ops import ExecParams
from ..ops import ProcsExecOps
from ..ops import format_exec_output


@pytest.mark.asyncs('asyncio')
async def test_procs_exec_ops_basic(tmp_path):
    async with procs.AsyncioProcessManager() as m:
        ops = ProcsExecOps()
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

from ....core import procs as _procs  # noqa: E402


@_dc.dataclass(frozen=True)
class _EchoSandbox(_procs.Sandbox):
    def transform_spec(self, spec):
        # observably wraps: echoes a marker to stderr, then execs the original command.
        return _dc.replace(spec, argv=['sh', '-c', 'echo SANDBOXED >&2; exec "$@"', 'sh', *spec.argv])


@pytest.mark.asyncs('asyncio')
async def test_procs_exec_ops_applies_options(tmp_path):
    async with procs.AsyncioProcessManager() as m:
        r = await ProcsExecOps().exec(m.root, ExecParams(
            ['echo', 'hi'],
            cwd=str(tmp_path),
            env={'PATH': '/usr/bin:/bin'},
            options=(_EchoSandbox(),),
        ))
        assert r.rc == 0
        assert r.stdout == b'hi\n'
        assert r.stderr == b'SANDBOXED\n'
