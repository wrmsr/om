import functools
import os
import shutil
import subprocess
import sys

import pytest

from ...asyncio.manager import AsyncioProcessManager
from ...types.specs import ProcessSpec
from ...types.specs import PtyStdio
from ..bwrap import BwrapSandbox
from ..bwrap import build_bwrap_argv
from ..bwrap import iter_symlink_prefixes
from ..policy import SandboxPolicy
from ..seatbelt import SeatbeltSandbox
from ..seatbelt import build_seatbelt_profile


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


def test_bwrap_dev_modes(tmp_path):
    argv = build_bwrap_argv('bwrap', SandboxPolicy(system_read_roots=[]))
    assert ['--dev', '/dev'] == argv[argv.index('--dev'):argv.index('--dev') + 2]  # 'minimal' default
    assert '--dev-bind' not in argv

    argv = build_bwrap_argv('bwrap', SandboxPolicy(system_read_roots=[], dev='all'))
    assert ['--dev-bind', '/dev', '/dev'] == argv[argv.index('--dev-bind'):argv.index('--dev-bind') + 3]

    argv = build_bwrap_argv('bwrap', SandboxPolicy(system_read_roots=[], dev='none'))
    assert '--dev' not in argv and '--dev-bind' not in argv

    argv = build_bwrap_argv('bwrap', SandboxPolicy(system_read_roots=[], private_tmp=False))
    assert '--tmpfs' not in argv


def test_bwrap_mounts_before_binds(tmp_path):
    # Regression: `--tmpfs /tmp` (and --dev/--proc) used to come *after* the binds, shadowing any root under /tmp - such
    # as every pytest tmp_path.
    root = tmp_path / 'r'
    root.mkdir()
    argv = build_bwrap_argv('bwrap', SandboxPolicy(read_roots=[str(root)], system_read_roots=[]))
    assert argv.index('--tmpfs') < argv.index('--ro-bind')
    assert argv.index('--dev') < argv.index('--ro-bind')
    assert argv.index('--proc') < argv.index('--ro-bind')


def test_bwrap_recreates_symlink_prefixes(tmp_path):
    # Regression: paths were bound only at their realpath, so on merged-/usr hosts `/lib64` (-> usr/lib64) never existed
    # in the sandbox and no dynamically linked binary could exec. Every symlink on the way to a root must be recreated
    # with --symlink, and the real path bound.
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
    assert out.cwd is None  # applied via --chdir


##


def test_sandbox_exec_profile(tmp_path):
    exe = tmp_path / 'rg'
    exe.write_text('')

    pol = SandboxPolicy(read_roots=['/a b'], write_roots=['/w'], system_read_roots=['/usr'])
    prof = build_seatbelt_profile(pol, argv0=str(exe))

    assert '(deny default)' in prof.profile

    # Caller paths travel as -D params, never through the profile text (spaces &c are structurally moot).
    assert '/a b' not in prof.profile
    vals = set(prof.params.values())
    assert '/a b' in vals
    assert '/w' in vals
    assert os.path.realpath(str(exe)) in vals

    # Exec is scoped to argv0's literal path(s); nothing broader is granted.
    assert '(allow process-exec (literal (param "EXEC_0"))' in prof.profile
    assert '(allow process-exec)' not in prof.profile
    assert '(allow process-fork)' not in prof.profile
    assert 'mach-lookup' not in prof.profile

    # Sysctl and metadata are scoped, not blanket - but the root dir itself is readable (libSystem startup needs it).
    assert '(allow sysctl-read)' not in prof.profile
    assert '(sysctl-name-prefix "hw.")' in prof.profile
    assert '(allow file-read-metadata' in prof.profile
    assert '(allow file-read* file-test-existence (literal "/"))' in prof.profile

    # Writes don't get the full file* wildcard.
    assert 'file-write*' in prof.profile
    assert '(allow file* ' not in prof.profile

    assert '(allow network*)' not in prof.profile

    # Opt-ins render.
    assert '(allow network*)' in build_seatbelt_profile(SandboxPolicy(allow_network=True), argv0=str(exe)).profile
    assert '(allow process-fork)' in build_seatbelt_profile(SandboxPolicy(allow_fork=True), argv0=str(exe)).profile
    assert '(allow sysctl-read)' in build_seatbelt_profile(SandboxPolicy(sysctl_names='any'), argv0=str(exe)).profile


def test_seatbelt_wraps_spec(tmp_path):
    exe = tmp_path / 'rg'
    exe.write_text('')

    pol = SandboxPolicy(read_roots=[str(tmp_path)], private_tmp=False)
    out = SeatbeltSandbox(policy=pol).transform_spec(ProcessSpec([str(exe), 'x']))
    assert out.argv[0] == '/usr/bin/sandbox-exec'
    assert out.argv[1] == '-D'
    assert '-p' in out.argv
    assert list(out.argv[-2:]) == [str(exe), 'x']
    assert out.env is None  # untouched without private_tmp

    # exec_paths='self' needs an absolute argv[0].
    with pytest.raises(ValueError):  # noqa: PT011
        SeatbeltSandbox(policy=pol).transform_spec(ProcessSpec(['rg', 'x']))


def test_seatbelt_private_tmp(tmp_path):
    exe = tmp_path / 'rg'
    exe.write_text('')

    out = SeatbeltSandbox(policy=SandboxPolicy(read_roots=[str(tmp_path)])).transform_spec(ProcessSpec([str(exe)]))
    assert out.env is not None
    td = out.env['TMPDIR']
    try:
        assert os.path.isdir(td)
        assert any(a.endswith(td) for a in out.argv if a.startswith(('WR_', 'META_')))  # granted via -D defs
    finally:
        shutil.rmtree(td, ignore_errors=True)


# pty adds nothing special to the sandbox wrapping, but the wrapped spec must keep its PtyStdio.
def test_sandbox_preserves_stdio(tmp_path):
    spec = ProcessSpec(['bash'], cwd=str(tmp_path), stdio=PtyStdio())
    out = BwrapSandbox(policy=SandboxPolicy(read_roots=[str(tmp_path)])).transform_spec(spec)
    assert isinstance(out.stdio, PtyStdio)


##


@functools.cache
def _bwrap_usable() -> bool:
    if not shutil.which('bwrap'):
        return False
    # Probe with our own rendering (a bare `--ro-bind /usr /usr` can't even exec /bin/true on a merged-/usr host).
    r = subprocess.run(  # noqa
        [*build_bwrap_argv('bwrap', SandboxPolicy(exec_paths='any')), 'true'],
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


@pytest.mark.skipif(sys.platform != 'darwin', reason='sandbox-exec is macOS-only')
@pytest.mark.asyncs('asyncio')
async def test_seatbelt_confinement_live(tmp_path):
    allowed = tmp_path / 'allowed'
    allowed.mkdir()
    (allowed / 'ok.txt').write_text('visible')
    secret = tmp_path / 'secret'
    secret.mkdir()
    (secret / 'nope.txt').write_text('hidden')

    async with AsyncioProcessManager() as m:
        pol = SandboxPolicy(read_roots=[str(allowed)], private_tmp=False)
        sandbox = SeatbeltSandbox(policy=pol)

        # can read the allowed root (via its as-given, possibly-symlinked pytest tmp path)
        run = await m.root.run(ProcessSpec(['/bin/cat', str(allowed / 'ok.txt')], cwd=str(allowed)), sandbox)
        assert run.returncode == 0 and run.stdout == b'visible'

        # cannot read outside it
        run = await m.root.run(ProcessSpec(['/bin/cat', str(secret / 'nope.txt')], cwd=str(allowed)), sandbox)
        assert run.returncode != 0
        assert b'hidden' not in run.stdout

        # exec is scoped to argv[0]: bash starts, but cannot exec anything else (and cannot fork)
        run = await m.root.run(ProcessSpec(['/bin/bash', '-c', '/usr/bin/true'], cwd=str(allowed)), sandbox)
        assert run.returncode != 0

        # no network (literal ip - no dns dependence)
        run = await m.root.run(ProcessSpec(['/usr/bin/nc', '-G', '2', '-z', '1.1.1.1', '80'], cwd=str(allowed)), sandbox)  # noqa: E501
        assert run.returncode != 0
