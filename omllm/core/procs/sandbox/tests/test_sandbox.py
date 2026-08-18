import functools
import shutil
import subprocess

import pytest

from ...asyncio.manager import AsyncioProcessManager
from ...types.specs import ProcessSpec
from ...types.specs import PtyStdio
from ..bwrap import BwrapSandbox
from ..bwrap import build_bwrap_argv
from ..policy import SandboxPolicy
from ..sandboxexec import SandboxExecSandbox
from ..sandboxexec import build_sandbox_exec_profile


def test_build_bwrap_argv(tmp_path):
    ro = tmp_path / 'ro'
    rw = tmp_path / 'rw'
    ro.mkdir()
    rw.mkdir()
    pol = SandboxPolicy(
        read_roots=[str(ro)],
        write_roots=[str(rw)],
        system_read_roots=['/usr', '/nonexistent-xyz'],
        allow_network=False,
    )
    argv = build_bwrap_argv('bwrap', pol, cwd=str(ro))

    assert argv[0] == 'bwrap'
    assert '--die-with-parent' in argv
    assert '--unshare-net' in argv                 # network denied
    assert argv[-1] == '--'

    def _pair(flag, path):
        return any(
            argv[i] == flag and argv[i + 1] == path and argv[i + 2] == path
            for i in range(len(argv) - 2)
        )

    assert _pair('--ro-bind', str(ro))             # read root bound ro
    assert _pair('--bind', str(rw))                # write root bound rw
    assert _pair('--ro-bind', '/usr')              # existing system root
    assert '/nonexistent-xyz' not in argv          # missing paths skipped (bwrap would error)
    assert ['--chdir', str(ro)] == argv[argv.index('--chdir'):argv.index('--chdir') + 2]

    # network allowed -> no --unshare-net
    argv2 = build_bwrap_argv('bwrap', SandboxPolicy(read_roots=[str(ro)], allow_network=True))
    assert '--unshare-net' not in argv2


def test_bwrap_wraps_spec(tmp_path):
    pol = SandboxPolicy(read_roots=[str(tmp_path)])
    spec = ProcessSpec(['rg', 'foo'], cwd=str(tmp_path))
    out = BwrapSandbox(policy=pol).transform_spec(spec)
    assert out.argv[0] == 'bwrap'
    assert list(out.argv[-2:]) == ['rg', 'foo']
    assert '--' in out.argv
    assert out.cwd is None                         # applied via --chdir


def test_sandbox_exec_profile():
    pol = SandboxPolicy(read_roots=['/a b'], write_roots=['/w'], system_read_roots=['/usr'], allow_network=False)
    prof = build_sandbox_exec_profile(pol)
    assert '(deny default)' in prof
    assert '(allow file-read* (subpath "/usr"))' in prof
    assert '(allow file-read* (subpath "/a b"))' in prof     # spaces handled
    assert '(allow file* (subpath "/w"))' in prof
    assert '(allow network*)' not in prof                    # denied

    argv = SandboxExecSandbox(policy=pol).transform_spec(ProcessSpec(['rg', 'x'])).argv
    assert argv[0] == '/usr/bin/sandbox-exec'
    assert argv[1] == '-p'
    assert list(argv[-2:]) == ['rg', 'x']

    prof2 = build_sandbox_exec_profile(SandboxPolicy(allow_network=True))
    assert '(allow network*)' in prof2


# pty adds nothing special to the sandbox wrapping, but the wrapped spec must keep its PtyStdio.
def test_sandbox_preserves_stdio(tmp_path):
    spec = ProcessSpec(['bash'], cwd=str(tmp_path), stdio=PtyStdio())
    out = BwrapSandbox(policy=SandboxPolicy(read_roots=[str(tmp_path)])).transform_spec(spec)
    assert isinstance(out.stdio, PtyStdio)


@functools.cache
def _bwrap_usable() -> bool:
    if not shutil.which('bwrap'):
        return False
    r = subprocess.run(  # noqa
        ['bwrap', '--ro-bind', '/usr', '/usr', '--unshare-net', '--die-with-parent', '--', '/bin/true'],
        capture_output=True,
    )
    return r.returncode == 0


@pytest.mark.skipif(not _bwrap_usable(), reason='bwrap cannot create user namespaces here')
@pytest.mark.asyncs('asyncio')
async def test_bwrap_confinement_live(tmp_path):
    allowed = tmp_path / 'allowed'
    allowed.mkdir()
    (allowed / 'ok.txt').write_text('visible')
    secret = tmp_path / 'secret'
    secret.mkdir()
    (secret / 'nope.txt').write_text('hidden')

    async with AsyncioProcessManager() as m:
        pol = SandboxPolicy(read_roots=[str(allowed)], allow_network=False)
        sandbox = BwrapSandbox(policy=pol)

        # can read the allowed root
        run = await m.root.run(ProcessSpec(['cat', str(allowed / 'ok.txt')], cwd=str(allowed)), sandbox)
        assert run.returncode == 0 and run.stdout == b'visible'

        # cannot read the unbound secret root
        run = await m.root.run(ProcessSpec(['cat', str(secret / 'nope.txt')], cwd=str(allowed)), sandbox)
        assert run.returncode != 0
        assert b'hidden' not in run.stdout

        # no network
        run = await m.root.run(
            ProcessSpec(['python3', '-c', 'import socket; socket.create_connection(("1.1.1.1", 80), 2)'],
                        cwd=str(allowed)),
            sandbox,
        )
        assert run.returncode != 0
