import asyncio
import os
import signal
import sys
import time

import pytest

from ...manager import ManagerConfig
from ...scopes.policies import ScopeClosePolicy
from ...spool.render import ArrivalMergedRenderer
from ...types.errors import ManagerNotStartedError
from ...types.errors import ProcessNotAliveError
from ...types.errors import ProcessTimeoutError
from ...types.errors import ScopeClosedError
from ...types.errors import SpawnError
from ...types.errors import StuckProcessError
from ...types.errors import UnsafeChildSignalDispositionError
from ...types.events import ProcessAbandonedEvent
from ...types.events import ProcessExitedEvent
from ...types.events import ProcessReapedEvent
from ...types.events import ProcessSpawnedEvent
from ...types.options import Credentials
from ...types.options import Rlimit
from ...types.options import SessionMode
from ...types.options import SpoolPolicy
from ...types.options import Tag
from ...types.options import TerminationPolicy
from ...types.options import Umask
from ...types.specs import ProcessSpec
from ...types.specs import ProcessStdio
from ...types.states import ProcessState
from ..manager import AsyncioProcessManager
from ..process import AsyncioProcess


def _sh(script, **kwargs):
    return ProcessSpec(['sh', '-c', script], **kwargs)


def _reaped(pid):
    # NB: must not reap - waitid(WNOWAIT) only peeks. (A plain waitpid(WNOHANG) here would steal the zombie and
    # correctly get the handle poisoned.)
    try:
        os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    except ChildProcessError:
        return True
    return False


def _pid_alive(pid):
    try:
        os.kill(pid, 0)  # only used on pids the test itself owns / just observed - test code only
    except ProcessLookupError:
        return False
    return True


async def _read_first_line(proc, timeout=5.):
    deadline = time.monotonic() + timeout
    buf = b''
    while time.monotonic() < deadline:
        r = proc.spool.read_available(0)
        buf = r.data()
        if b'\n' in buf:
            return buf.split(b'\n', 1)[0]
        await asyncio.sleep(.02)
    raise AssertionError(f'no line within {timeout}s (got {buf!r})')


async def _poll(fn, timeout=5., interval=.02):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        await asyncio.sleep(interval)
    return fn()


##


@pytest.mark.asyncs('asyncio')
async def test_run_basic():
    async with AsyncioProcessManager() as m:
        run = await m.root.run(_sh('echo out1; echo err1 >&2; echo out2; exit 3', name='demo'))
        assert run.returncode == 3
        assert run.stdout == b'out1\nout2\n'
        assert run.stderr == b'err1\n'
        assert run.output.ended
        assert run.process.state.name == 'REAPED'
        assert run.process.name == 'demo'
        assert not m.processes
        assert _reaped(run.process.pid)
        assert ArrivalMergedRenderer().render(run.output.records).count('\n') == 3

        # Signaled exit reports negative signal number.
        run = await m.root.run(_sh('kill -TERM $$'))
        assert run.returncode == -signal.SIGTERM
    assert m.closed


@pytest.mark.asyncs('asyncio')
async def test_env_cwd_umask_rlimit():
    async with AsyncioProcessManager() as m:
        run = await m.root.run(ProcessSpec(
            ['sh', '-c', 'echo $FOO; echo ${HOME-unset}; pwd; umask; ulimit -n'],
            env={'FOO': 'bar', 'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            cwd='/',
        ), Umask(0o077), Rlimit(__import__('resource').RLIMIT_NOFILE, 321, 321))
        assert run.stdout.split(b'\n')[:5] == [b'bar', b'unset', b'/', b'0077', b'321']

        # env=None inherits our environ.
        os.environ['OM_PROCS_TEST_ENV'] = 'yes'
        try:
            run = await m.root.run(_sh('echo $OM_PROCS_TEST_ENV'))
        finally:
            del os.environ['OM_PROCS_TEST_ENV']
        assert run.stdout == b'yes\n'


@pytest.mark.asyncs('asyncio')
async def test_session_modes():
    async with AsyncioProcessManager() as m:
        code = 'import os; print(os.getpgrp() == os.getpid(), os.getsid(0) == os.getpid())'
        run = await m.root.run(ProcessSpec([sys.executable, '-c', code]))
        assert run.stdout == b'True True\n'
        run = await m.root.run(ProcessSpec([sys.executable, '-c', code]), SessionMode(mode='group'))
        assert run.stdout == b'True False\n'


@pytest.mark.asyncs('asyncio')
async def test_stdin_and_exit_without_reap():
    async with AsyncioProcessManager() as m:
        p = await m.root.spawn(ProcessSpec(['cat'], stdio=ProcessStdio(stdin='pipe')))
        assert p.state.name == 'RUNNING'
        assert p.has_stdin
        await p.write(b'hello\n')
        r = await p.spool.read(0, wait=2., max_bytes=6)
        assert r.data() == b'hello\n'
        assert not r.ended
        await p.write_eof()
        assert await p.wait(5.) == 0
        # Exited but deliberately not reaped: pid still ours.
        assert p.state.name == 'EXITED'
        assert p.exited
        assert not _reaped(p.pid)
        if sys.platform.startswith('linux'):
            with open(f'/proc/{p.pid}/stat') as f:  # noqa: ASYNC230
                assert f.read().split(') ')[1].startswith('Z')
        # Signals still allowed while unreaped (harmless to a zombie).
        await p.signal(signal.SIGTERM)
        assert await p.wait_output_ended(2.)
        await p.aclose()
        assert p.state.name == 'REAPED'
        assert _reaped(p.pid)
        with pytest.raises(ProcessNotAliveError):
            await p.signal(signal.SIGTERM)
        with pytest.raises(BrokenPipeError):
            await p.write(b'x')
        # Idempotent.
        await p.aclose()


@pytest.mark.asyncs('asyncio')
async def test_escalation_kills_group():
    async with AsyncioProcessManager() as m:
        p = await m.root.spawn(
            _sh('trap "" TERM; sleep 100 & echo $!; while :; do sleep 0.05; done'),
            TerminationPolicy(grace_s=.2),
        )
        gpid = int(await _read_first_line(p))
        assert _pid_alive(gpid)
        t0 = time.monotonic()
        await p.aclose()
        assert time.monotonic() - t0 < 3.
        assert p.state.name == 'REAPED'
        assert p.returncode == -signal.SIGKILL
        assert await _poll(lambda: not _pid_alive(gpid))


@pytest.mark.asyncs('asyncio')
async def test_setsid_grandchild_not_ours():
    async with AsyncioProcessManager() as m:
        code = 'import os,time; os.setsid(); print(os.getpid(), flush=True); time.sleep(3)'
        p = await m.root.spawn(_sh(f'{sys.executable} -c "{code}" & sleep 100'))
        gpid = int(await _read_first_line(p))
        assert _pid_alive(gpid)
        await p.aclose(TerminationPolicy(grace_s=.2, drain_s=.2))
        assert p.state.name == 'REAPED'
        # Escaped the group: not signaled by us, still alive right after close - it exits on its own.
        assert _pid_alive(gpid)
        assert await _poll(lambda: not _pid_alive(gpid), timeout=10.)


@pytest.mark.asyncs('asyncio')
async def test_run_timeout():
    async with AsyncioProcessManager() as m:
        with pytest.raises(ProcessTimeoutError):
            await m.root.run(_sh('sleep 10'), timeout=.2)
        assert not m.processes

        # And via the RunTimeout option
        from ...types.options import RunTimeout
        with pytest.raises(ProcessTimeoutError):
            await m.root.run(_sh('sleep 10'), RunTimeout(.2))
        assert not m.processes


@pytest.mark.asyncs('asyncio')
async def test_spawn_errors():
    events: list = []
    async with AsyncioProcessManager() as m:
        m.subscribe(events.append)
        with pytest.raises(SpawnError) as ei:
            await m.root.spawn(ProcessSpec(['/nonexistent/prog']))
        assert ei.value.stage == 'exec'
        assert ei.value.errno == 2
        assert not m.processes

        with pytest.raises(SpawnError) as ei:
            await m.root.spawn(ProcessSpec(['true'], cwd='/nonexistent/dir'))
        assert ei.value.stage == 'chdir'
        assert not m.processes
    assert not [e for e in events if isinstance(e, ProcessSpawnedEvent)]
    assert len([e for e in events if isinstance(e, ProcessReapedEvent)]) == 2


@pytest.mark.asyncs('asyncio')
async def test_scopes_and_backgrounding():
    events: list = []
    async with AsyncioProcessManager() as m:
        m.subscribe(events.append)
        async with m.root.child('agent', options=[Tag('agent')]) as agent:
            async with agent.child('turn') as turn:
                async with turn.child('tool') as tool:
                    fg = await tool.spawn(_sh('sleep 100'))
                    bg = await tool.spawn(_sh('while :; do echo tick; sleep 0.02; done'))
                    assert list(bg.options[Tag]) == [Tag('agent')]
                    assert tool.path == ('root', 'agent', 'turn', 'tool')
                    agent.adopt(bg)
                    assert bg.scope is agent
                    assert bg.id in agent.processes and bg.id not in tool.processes
                    await tool.aclose()
                    with pytest.raises(ScopeClosedError):
                        await tool.spawn(_sh('true'))
                # tool scope closed: fg gone, bg alive.
                assert fg.state.name == 'REAPED'
                assert bg.state.name == 'RUNNING'
                assert tool.closed and 'tool' not in turn.children
            r = await bg.spool.read(0, wait=.2)
            assert r.data().count(b'tick') >= 2
        assert bg.state.name == 'REAPED'
        assert not m.processes
    kinds = [type(e).__name__ for e in events]
    assert kinds.index('ProcessReparentedEvent') < kinds.index('ScopeClosedEvent')


@pytest.mark.asyncs('asyncio')
async def test_big_output_spills_and_cursor_reads(tmp_path):
    async with AsyncioProcessManager(ManagerConfig(spill_dir=str(tmp_path))) as m:
        n = 3 * 1024 * 1024
        p = await m.root.spawn(
            _sh(f'head -c {n} /dev/zero | tr "\\0" x; echo; echo done >&2'),
            SpoolPolicy(memory_cap=256 * 1024),
        )
        await p.wait(30.)
        await p.aclose()
        sp = p.spool
        assert sp.ended
        assert sp.payload_total == n + 1 + 5
        assert sp.storage.spilled_end > 0
        assert sp.spill_path is not None and os.path.exists(sp.spill_path)
        spill_path = sp.spill_path

        total = 0
        cur = 0
        reads = 0
        while True:
            r = sp.read_available(cur, max_bytes=100_000)
            if not r.records:
                assert r.ended
                break
            assert r.dropped_before == 0
            total += sum(len(x.data) for x in r.records)
            cur = r.end
            reads += 1
        assert total == n + 6
        assert reads >= 15

        # Dropping (no spill) reports dropped_before.
        p2 = await m.root.spawn(
            _sh(f'head -c {n} /dev/zero | tr "\\0" y'),
            SpoolPolicy(memory_cap=64 * 1024, spill=False),
        )
        await p2.wait(30.)
        await p2.aclose()
        r = p2.spool.read_available(0)
        assert r.dropped_before > 0
        assert r.dropped_before + sum(len(x.data) for x in r.records) + 32 * len(r.records) <= p2.spool.total
    assert not os.path.exists(spill_path)  # closed and not kept


@pytest.mark.asyncs('asyncio')
async def test_wait_cancellation_and_concurrency():
    async with AsyncioProcessManager() as m:
        p = await m.root.spawn(_sh('sleep 100'))
        t = asyncio.ensure_future(p.wait())
        await asyncio.sleep(.05)
        t.cancel()
        with pytest.raises(asyncio.CancelledError):
            await t
        assert p.state.name == 'RUNNING'
        await p.aclose(TerminationPolicy(grace_s=1.))
        assert p.state.name == 'REAPED'

        runs = await asyncio.gather(*[
            m.root.run(_sh(f'echo {i}; exit {i % 3}'))
            for i in range(20)
        ])
        assert [r.stdout for r in runs] == [f'{i}\n'.encode() for i in range(20)]
        assert [r.returncode for r in runs] == [i % 3 for i in range(20)]
        assert all(_reaped(r.process.pid) for r in runs)
        assert not m.processes


@pytest.mark.asyncs('asyncio')
async def test_stuck_abandonment():
    events: list = []
    async with AsyncioProcessManager() as m:
        m.subscribe(events.append)
        # kill_s=0: SIGKILL is sent and not waited for, exercising the abandonment path deterministically.
        p = await m.root.spawn(
            _sh('trap "" TERM; echo ready; while :; do sleep 0.05; done'),
            TerminationPolicy(grace_s=.1, kill_s=0),
        )
        await _read_first_line(p)
        await p.aclose()
        assert p.state in (ProcessState.ABANDONED, ProcessState.EXITED, ProcessState.REAPED)
        assert p.id not in m.processes
        # The lingering watcher finishes it off once it actually dies.
        assert await _poll(lambda: p.state.name == 'REAPED')
        assert _reaped(p.pid)

        p2 = await m.root.spawn(
            _sh('trap "" TERM; echo ready; while :; do sleep 0.05; done'),
            TerminationPolicy(grace_s=.1, kill_s=0, on_stuck='raise'),
        )
        await _read_first_line(p2)
        with pytest.raises(StuckProcessError):
            await p2.aclose()
        assert await _poll(lambda: p2.state.name == 'REAPED')
    assert any(isinstance(e, ProcessAbandonedEvent) for e in events)


@pytest.mark.asyncs('asyncio')
async def test_scope_close_policy_backstop():
    async with AsyncioProcessManager(ManagerConfig(close_policy=ScopeClosePolicy(overall_timeout_s=.3))) as m:
        s = m.root.child('s')
        p = await s.spawn(_sh('trap "" TERM; echo ready; while :; do sleep 0.05; done'), TerminationPolicy(grace_s=10.))
        await _read_first_line(p)
        t0 = time.monotonic()
        await s.aclose()
        assert time.monotonic() - t0 < 3.
        assert p.state in (ProcessState.ABANDONED, ProcessState.EXITED, ProcessState.REAPED)
        assert not m.processes
        # The abandoned process is still ours (unreaped) - closing the manager must not hang, and the watcher reaps
        # it once the SIGKILL from the abandonment... note: no SIGKILL was sent by the backstop; send one ourselves.
        if p.state.name == 'ABANDONED':
            await p.kill()
        assert await _poll(lambda: p.state.name == 'REAPED')


@pytest.mark.asyncs('asyncio')
async def test_manager_lifecycle():
    m = AsyncioProcessManager()
    with pytest.raises(ManagerNotStartedError):
        await m.root.spawn(_sh('true'))
    await m.start()
    assert m.started
    run = await m.root.run(_sh('true'))
    assert run.returncode == 0
    sd = m.spill_dir
    assert sd is not None and os.path.isdir(sd)
    await m.aclose()
    assert m.closed
    assert not os.path.exists(sd)
    await m.aclose()

    # A fresh instance works after the previous one closed.
    async with AsyncioProcessManager() as m2:
        assert (await m2.root.run(_sh('echo again'))).stdout == b'again\n'


@pytest.mark.asyncs('asyncio')
async def test_zombie_signal_eperm_tolerated(monkeypatch):
    # macOS/BSD return EPERM (not ESRCH) when signaling a zombie or an all-zombie group. Inject that here so the
    # behavior is exercised on any platform: it must be swallowed for a process we hold that has already exited, but
    # surfaced for one that is genuinely still alive.
    async with AsyncioProcessManager() as m:
        exited = await m.root.spawn(_sh('exit 0'))
        assert await exited.wait(5.) == 0
        assert exited.state.name == 'EXITED'  # a real, still-held zombie

        def _eperm(*_a, **_k):
            raise PermissionError(1, 'Operation not permitted')

        monkeypatch.setattr(os, 'killpg', _eperm)
        monkeypatch.setattr(os, 'kill', _eperm)

        # Confirmed-dead target: EPERM is the benign zombie quirk -> swallowed.
        await exited.signal(signal.SIGTERM)
        await exited.signal(signal.SIGTERM, process_group=False)
        await exited.aclose()  # the group sweep also EPERMs and must not raise
        assert exited.state.name == 'REAPED'

        # Live target: EPERM is genuine -> surfaced.
        alive = await m.root.spawn(_sh('sleep 100'))
        await _poll(lambda: alive.state.name == 'RUNNING')
        with pytest.raises(PermissionError):
            await alive.signal(signal.SIGTERM)

        monkeypatch.undo()
        await alive.aclose()
        assert alive.state.name == 'REAPED'


def test_is_exited_nowait():
    import subprocess
    p = subprocess.Popen(['sh', '-c', 'exit 0'])
    p.wait()  # reaped by Popen -> gone
    assert AsyncioProcess._is_exited_nowait(p.pid) is True  # noqa: SLF001

    p2 = subprocess.Popen(['sh', '-c', 'sleep 100'])
    try:
        assert AsyncioProcess._is_exited_nowait(p2.pid) is False  # noqa: SLF001
    finally:
        p2.kill()
        p2.wait()


def test_sigchld_guard():
    old = signal.getsignal(signal.SIGCHLD)
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    try:
        with pytest.raises(UnsafeChildSignalDispositionError):
            AsyncioProcessManager.check_child_signal_disposition()
    finally:
        signal.signal(signal.SIGCHLD, old if old is not None else signal.SIG_DFL)
    AsyncioProcessManager.check_child_signal_disposition()


@pytest.mark.skipif(os.geteuid() != 0, reason='requires root')
@pytest.mark.asyncs('asyncio')
async def test_credentials_drop():
    import pwd
    nobody = pwd.getpwnam('nobody')
    async with AsyncioProcessManager() as m:
        run = await m.root.run(ProcessSpec(['id', '-u']), Credentials(user='nobody'))
        assert run.stdout.strip() == str(nobody.pw_uid).encode()
        run = await m.root.run(ProcessSpec(['id', '-g']), Credentials(user=nobody.pw_uid))
        assert run.stdout.strip() == str(nobody.pw_gid).encode()


@pytest.mark.asyncs('asyncio')
async def test_events_order():
    events: list = []
    async with AsyncioProcessManager() as m:
        m.subscribe(events.append)
        run = await m.root.run(_sh('true'))
    pe = [e for e in events if getattr(e, 'process_id', None) == run.process.id]
    assert [type(e) for e in pe] == [ProcessSpawnedEvent, ProcessExitedEvent, ProcessReapedEvent]
    assert pe[1].returncode == 0
