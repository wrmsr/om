import asyncio
import os
import signal
import sys

import pytest

from ...managers.pty import PTY_OUTPUT_FD
from ...spool.render import RawRenderer
from ...types.errors import NotAPtyError
from ...types.specs import ProcessSpec
from ...types.specs import PtyStdio
from ...types.states import ProcessState
from ..manager import AsyncioProcessManager
from .utils import disable_posix_spawn_setsid


async def _poll(fn, timeout=5., interval=.02):
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if fn():
            return True
        await asyncio.sleep(interval)
    return fn()


@pytest.mark.asyncs('asyncio')
async def test_pty_controlling_terminal_and_winsize():
    async with AsyncioProcessManager() as m:
        run = await m.root.run(ProcessSpec(
            ['sh', '-c', 'tty; stty size; echo "TERM=$TERM"; ps -o tty= -p $$'],
            stdio=PtyStdio(rows=30, cols=100),
        ))
        assert run.returncode == 0
        out = RawRenderer().render(run.output.records)
        lines = out.splitlines()
        assert lines[0].startswith('/dev/')       # stdin is a tty
        assert lines[1] == '30 100'               # winsize propagated
        assert lines[2] == 'TERM=xterm-256color'  # TERM injected
        assert lines[3].strip() not in ('?', '')  # a real controlling terminal (not '?')
        # pty output is a single merged stream tagged as fd 1.
        assert all(r.fd == PTY_OUTPUT_FD for r in run.output.records)
        assert run.process.has_pty


@pytest.mark.asyncs('asyncio')
@pytest.mark.skipif(sys.platform != 'linux', reason='linux only')
async def test_pty_controlling_terminal_with_shim_setsid_fallback(monkeypatch):
    disable_posix_spawn_setsid(monkeypatch)

    async with AsyncioProcessManager() as m:
        run = await m.root.run(ProcessSpec(
            ['sh', '-c', 'tty; ps -o sid= -p $$; ps -o pgid= -p $$; echo $$'],
            stdio=PtyStdio(),
        ))
        assert run.returncode == 0
        lines = RawRenderer().render(run.output.records).splitlines()
        assert lines[0].startswith('/dev/')
        assert len({line.strip() for line in lines[1:]}) == 1


@pytest.mark.asyncs('asyncio')
async def test_pty_interactive_echo_and_resize():
    async with AsyncioProcessManager() as m:
        p = await m.root.spawn(ProcessSpec(['cat'], stdio=PtyStdio(rows=24, cols=80)))
        assert p.has_pty
        assert p.has_stdin
        assert p.get_winsize() == (24, 80)

        await p.write(b'hello\n')
        # cooked-mode tty echoes input (\r\n), and cat echoes it again.
        assert await _poll(lambda: p.spool.read_available(0).data().count(b'hello') >= 2)
        assert b'\r\n' in p.spool.read_available(0).data()

        await p.resize(40, 120)
        assert p.get_winsize() == (40, 120)

        await p.aclose()
        assert p.state is ProcessState.REAPED
        assert p.returncode == -signal.SIGTERM
        # has_pty stays true (a launched-under-pty fact); the fd is gone so winsize is None.
        assert p.has_pty
        assert p.get_winsize() is None


@pytest.mark.asyncs('asyncio')
async def test_pty_exit_ends_output():
    async with AsyncioProcessManager() as m:
        p = await m.root.spawn(ProcessSpec(['sh', '-c', 'echo done; exit 0'], stdio=PtyStdio()))
        assert await p.wait(5.) == 0
        # On Linux the master read gets EIO when the slave closes; it must resolve to a clean output-end.
        assert await p.wait_output_ended(5.)
        await p.aclose()
        assert b'done' in p.spool.read_available(0).data()
        assert not m.processes


@pytest.mark.asyncs('asyncio')
async def test_resize_requires_pty():
    async with AsyncioProcessManager() as m:
        p = await m.root.spawn(ProcessSpec(['sleep', '100']))
        assert not p.has_pty
        assert p.get_winsize() is None
        with pytest.raises(NotAPtyError):
            await p.resize(10, 10)
        await p.aclose()


@pytest.mark.asyncs('asyncio')
async def test_pty_term_overrides_host(monkeypatch):
    # Regression: PtyStdio.term must be authoritative even when the host already exports TERM (this used to flake - the
    # injection was skipped whenever the inherited environment had TERM set).
    monkeypatch.setenv('TERM', 'xterm')

    async with AsyncioProcessManager() as m:
        run = await m.root.run(ProcessSpec(['sh', '-c', 'echo TERM=$TERM'], stdio=PtyStdio()))
        assert RawRenderer().render(run.output.records).strip() == 'TERM=xterm-256color'

        # an explicit TERM in the spec env wins over the pty default
        run = await m.root.run(ProcessSpec(
            ['sh', '-c', 'echo TERM=$TERM'],
            env={'TERM': 'vt100', 'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            stdio=PtyStdio(),
        ))
        assert RawRenderer().render(run.output.records).strip() == 'TERM=vt100'

        # term=None leaves the inherited host TERM untouched
        run = await m.root.run(ProcessSpec(['sh', '-c', 'echo TERM=$TERM'], stdio=PtyStdio(term=None)))
        assert RawRenderer().render(run.output.records).strip() == 'TERM=xterm'
