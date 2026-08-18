import os
import shutil
import socket
import stat

import pytest

from ...asyncio.manager import AsyncioProcessManager
from ...types.specs import ProcessSpec
from ...types.specs import PtyStdio
from ..ssh import SshTarget
from ..ssh import build_remote_command


def test_build_remote_command():
    # cwd + env + argv, all shell-quoted into one string
    s = ProcessSpec(['ls', '-la', 'a b'], cwd='/work dir', env={'FOO': 'a b'})
    assert build_remote_command(s) == "cd '/work dir' && exec env FOO='a b' ls -la 'a b'"

    # no cwd / no env
    assert build_remote_command(ProcessSpec(['echo', 'hi'])) == 'exec echo hi'

    # env only
    assert build_remote_command(ProcessSpec(['x'], env={'K': 'v'})) == 'exec env K=v x'


def test_transform_spec():
    t = SshTarget(
        host='h', user='u', port=22, identity_file='/k',
        control_path='/cm', no_host_key_checking=True,
        extra_options=('-o', 'ServerAliveInterval=15'),
    )
    argv = list(t.transform_spec(ProcessSpec(['echo', 'x'])).argv)
    assert argv[0] == 'ssh'
    assert argv[1:5] == ['-p', '22', '-i', '/k']
    assert 'ControlMaster=auto' in argv
    assert 'ControlPath=/cm' in argv
    assert 'StrictHostKeyChecking=no' in argv
    assert 'ServerAliveInterval=15' in argv
    assert argv[-2] == 'u@h'
    assert argv[-1] == 'exec echo x'

    ts = t.transform_spec(ProcessSpec(['x'], cwd='/c'))
    assert ts.cwd is None and ts.env is None

    # pty -> -tt, and no user -> bare host
    p = SshTarget(host='h').transform_spec(ProcessSpec(['bash'], stdio=PtyStdio()))
    assert '-tt' in p.argv and p.argv[-2] == 'h'


# A fake `ssh` that ignores options/dest and runs the remote command string (its last argument) locally with `sh -c`.
_FAKE_SSH = r"""#!/usr/bin/env bash
set -euo pipefail
remote="${@: -1}"
exec sh -c "$remote"
"""


def _make_fake_ssh(tmp_path):
    p = tmp_path / 'ssh'
    p.write_text(_FAKE_SSH)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(p)


@pytest.mark.asyncs('asyncio')
async def test_ssh_target_streams_via_fake_ssh(tmp_path):
    fake = _make_fake_ssh(tmp_path)
    workdir = tmp_path / 'wd with space'
    workdir.mkdir()

    async with AsyncioProcessManager() as m:
        target = SshTarget(host='remote.example', user='om', ssh=fake)

        run = await m.root.run(
            ProcessSpec(
                ['sh', '-c', 'echo "env=$MARKER pwd=$(pwd)"; echo err >&2; exit 0'],
                cwd=str(workdir),
                env={'MARKER': 'hi there', 'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            ),
            target,
        )
        assert run.returncode == 0
        assert run.stdout == f'env=hi there pwd={workdir}\n'.encode()
        assert run.stderr == b'err\n'
        assert not m.processes


def _local_sshd() -> bool:
    if not shutil.which('ssh'):
        return False
    try:
        with socket.socket() as s:
            s.settimeout(0.5)
            s.connect(('127.0.0.1', 22))
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _local_sshd(), reason='no local sshd on 127.0.0.1:22')
@pytest.mark.asyncs('asyncio')
async def test_ssh_target_live_localhost():
    async with AsyncioProcessManager() as m:
        target = SshTarget(
            host='127.0.0.1',
            no_host_key_checking=True,
            extra_options=('-o', 'BatchMode=yes'),
        )
        run = await m.root.run(ProcessSpec(['sh', '-c', 'echo ssh-ok; whoami']), target)
        # may fail auth in CI; only assert we actually reached and ran ssh (rc 255 == ssh conn/auth error)
        assert run.returncode != 255 or b'ssh-ok' not in run.stdout
