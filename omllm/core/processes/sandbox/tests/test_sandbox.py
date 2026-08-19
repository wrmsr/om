import functools
import os
import shutil
import subprocess

import pytest

from ...asyncio.manager import AsyncioProcessManager
from ...types.specs import ProcessSpec
from ...types.specs import PtyStdio
from ..bwrap import BwrapSandbox
from ..bwrap import build_bwrap_argv
from ..bwrap import iter_symlink_prefixes
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

    assert _pair('--ro-bind', str(ro))       # read root bound ro
    assert _pair('--bind', str(rw))          # write root bound rw
    assert _pair('--ro-bind', '/usr')  # existing system root
    assert '/nonexistent-xyz' not in argv          # missing paths skipped (bwrap would error)
    assert ['--chdir', str(ro)] == argv[argv.index('--chdir'):argv.index('--chdir') + 2]

    # network allowed -> no --unshare-net
    argv2 = build_bwrap_argv('bwrap', SandboxPolicy(read_roots=[str(ro)], allow_network=True))
    assert '--unshare-net' not in argv2

    # --new-session is opt-in (it would detach a pty and swallow our TERM).
    assert '--new-session' not in argv
    assert '--new-session' in build_bwrap_argv('bwrap', pol, new_session=True)


def test_bwrap_mounts_before_binds(tmp_path):
    # Regression: `--tmpfs /tmp` (and --dev/--proc) used to come *after* the binds, shadowing any root under /tmp -
    # such as every pytest tmp_path.
    root = tmp_path / 'r'
    root.mkdir()
    argv = build_bwrap_argv('bwrap', SandboxPolicy(read_roots=[str(root)], system_read_roots=[]))
    assert argv.index('--tmpfs') < argv.index('--ro-bind')
    assert argv.index('--dev') < argv.index('--ro-bind')
    assert argv.index('--proc') < argv.index('--ro-bind')


def test_bwrap_recreates_symlink_prefixes(tmp_path):
    # Regression: paths were bound only at their realpath, so on merged-/usr hosts `/lib64` (-> usr/lib64) never
    # existed in the sandbox and no dynamically linked binary could exec. Every symlink on the way to a root must be
    # recreated with --symlink, and the real path bound.
    real = tmp_path / 'real'
    (real / 'sub').mkdir(parents=True)
    link = tmp_path / 'link'
    link.symlink_to('real')  # relative target, like /lib64 -> usr/lib64

    assert list(iter_symlink_prefixes(str(link / 'sub'))) == [('real', str(link))]
    assert list(iter_symlink_prefixes(str(real / 'sub'))) == []

    argv = build_bwrap_argv(
        'bwrap',
        SandboxPolicy(read_roots=[str(link / 'sub')], write_roots=[str(link)], system_read_roots=[]),
        cwd=str(link / 'sub'),
    )
    i = argv.index('--symlink')
    assert argv[i:i + 3] == ['--symlink', 'real', str(link)]
    assert argv.count('--symlink') == 1  # deduplicated across roots and cwd
    j = argv.index('--ro-bind')
    assert argv[j:j + 3] == ['--ro-bind', str(real / 'sub'), str(real / 'sub')]
    k = argv.index('--bind')
    assert argv[k:k + 3] == ['--bind', str(real), str(real)]
    # cwd keeps its given (symlinked) name - it resolves once the prefixes exist.
    c = argv.index('--chdir')
    assert argv[c + 1] == str(link / 'sub')

    # The real thing, on a merged-/usr host.
    if os.path.islink('/lib64'):
        argv = build_bwrap_argv('bwrap', SandboxPolicy(system_read_roots=['/usr', '/lib64']))
        i = argv.index('--symlink')
        assert argv[i:i + 3] == ['--symlink', os.readlink('/lib64'), '/lib64']


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
    assert '(allow file-read* (subpath "/a b"))' in prof  # spaces handled
    assert '(allow file* (subpath "/w"))' in prof
    assert '(allow network*)' not in prof                 # denied

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
    # Probe with our own rendering (a bare `--ro-bind /usr /usr` can't even exec /bin/true on a merged-/usr host).
    r = subprocess.run(  # noqa
        [*build_bwrap_argv('bwrap', SandboxPolicy()), 'true'],
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
            ProcessSpec(
                [
                    'python3',
                    '-c',
                    'import socket; socket.create_connection(("1.1.1.1", 80), 2)',
                ],
                cwd=str(allowed)),
            sandbox,
        )
        assert run.returncode != 0
