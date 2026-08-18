import os
import shutil
import socket
import stat
import subprocess
import time

import pytest

from ...asyncio.manager import AsyncioProcessManager
from ...types.specs import ProcessSpec
from ...types.specs import PtyStdio
from ..docker import DockerExecTarget


def test_transform_spec():
    t = DockerExecTarget(container='dev', user='1000:1000', extra_flags=('--privileged',))
    s = ProcessSpec(['ls', '-la'], cwd='/work', env={'FOO': 'bar', 'BAZ': 'qux'})
    argv = list(t.transform_spec(s).argv)
    assert argv == [
        'docker', 'exec', '-i', '--privileged', '-w', '/work', '-u', '1000:1000',
        '-e', 'FOO=bar', '-e', 'BAZ=qux', 'dev', '--', 'ls', '-la',
    ]
    # cwd/env are consumed into flags; the local client runs anywhere and inherits host env.
    ts = t.transform_spec(s)
    assert ts.cwd is None
    assert ts.env is None

    # pty adds -t
    p = DockerExecTarget(container='dev').transform_spec(ProcessSpec(['bash'], stdio=PtyStdio()))
    assert list(p.argv) == ['docker', 'exec', '-i', '-t', 'dev', '--', 'bash']

    # no env / no cwd -> minimal
    m = DockerExecTarget(container='dev').transform_spec(ProcessSpec(['true']))
    assert list(m.argv) == ['docker', 'exec', '-i', 'dev', '--', 'true']


# A fake `docker` that emulates `docker exec [-i|-t|-w D|-u U|-e K=V]... <container> -- <cmd...>` by running <cmd>
# locally (honoring -w and -e). Lets us exercise the full Target -> spawn -> stream path with no daemon.
_FAKE_DOCKER = r"""#!/usr/bin/env bash
set -euo pipefail
[ "$1" = exec ] || { echo "fake-docker: expected exec, got $1" >&2; exit 2; }
shift
declare -a envs=()
workdir=""
while [ $# -gt 0 ]; do
  case "$1" in
    -i|-t) shift ;;
    -w) workdir="$2"; shift 2 ;;
    -u) shift 2 ;;
    -e) envs+=("$2"); shift 2 ;;
    --) shift; break ;;
    *) container="$1"; shift ;;  # the container arg, then expect --
  esac
done
[ -n "${workdir:-}" ] && cd "$workdir"
exec env "${envs[@]}" "$@"
"""


def _make_fake_docker(tmp_path):
    p = tmp_path / 'docker'
    p.write_text(_FAKE_DOCKER)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(p)


@pytest.mark.asyncs('asyncio')
async def test_docker_exec_target_streams_via_fake_docker(tmp_path):
    fake = _make_fake_docker(tmp_path)
    workdir = tmp_path / 'wd'
    workdir.mkdir()

    async with AsyncioProcessManager() as m:
        target = DockerExecTarget(container='cid123', docker=fake)

        run = await m.root.run(
            ProcessSpec(
                ['sh', '-c', 'echo "in=$MARKER pwd=$(pwd)"; echo err >&2; exit 0'],
                cwd=str(workdir),
                env={'MARKER': 'hello', 'PATH': os.environ.get('PATH', '/usr/bin:/bin')},
            ),
            target,
        )
        assert run.returncode == 0
        assert run.stdout == f'in=hello pwd={workdir}\n'.encode()
        assert run.stderr == b'err\n'
        assert not m.processes


def _docker_daemon_up() -> bool:
    if not shutil.which('docker'):
        return False
    sock = '/var/run/docker.sock'
    if os.path.exists(sock):
        try:
            with socket.socket(socket.AF_UNIX) as s:
                s.settimeout(1.0)
                s.connect(sock)
            return True
        except OSError:
            return False
    return subprocess.run(['docker', 'info'], capture_output=True).returncode == 0  # noqa


def _wait_container_ready(cid: str, timeout: float = 20.0) -> bool:
    # `docker run -d` returns before the container is fully up; exec'ing too early gives a transient
    # "OCI runtime exec failed". Probe with a trivial exec until it succeeds.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if subprocess.run(['docker', 'exec', cid, 'true'], capture_output=True, check=False).returncode == 0:  # noqa
            return True
        time.sleep(0.1)
    return False


@pytest.mark.skipif(not _docker_daemon_up(), reason='no docker daemon')
@pytest.mark.asyncs('asyncio')
async def test_docker_exec_target_live():
    # Start a throwaway container, exec into it through the Target, and stream output.
    cid = subprocess.check_output(  # noqa: ASYNC221
        ['docker', 'run', '-d', '--rm', 'busybox', 'sleep', '60'],
    ).decode().strip()
    try:
        if not _wait_container_ready(cid):
            pytest.skip('container did not become exec-ready')

        async with AsyncioProcessManager() as m:
            run = await m.root.run(
                ProcessSpec(['sh', '-c', 'echo container-ok; hostname'], env={'X': 'y'}),
                DockerExecTarget(container=cid),
            )
            assert run.returncode == 0
            assert b'container-ok' in run.stdout
    finally:
        subprocess.run(['docker', 'kill', cid], capture_output=True, check=False)  # noqa: ASYNC221
