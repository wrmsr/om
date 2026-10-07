import os
import shutil
import socket
import stat
import subprocess
import time

import pytest

from omcore.os.pyremote.bestpython import get_best_python_sh
from omcore.os.pyremote.core import pyremote_build_bootstrap_source

from ....core import processes
from ..docker import DockerContainerIdt
from ..docker import DockerRemoteAgentConfig
from ..docker import DockerRemoteAgentConnection
from ..docker import DockerRemoteAgentError
from ..docker import build_docker_remote_agent_argv


def test_build_docker_remote_agent_argv():
    assert build_docker_remote_agent_argv(
        DockerContainerIdt('container-id'),
        DockerRemoteAgentConfig(docker='/usr/local/bin/docker'),
    ) == (
        '/usr/local/bin/docker',
        'exec',
        '-i',
        'container-id',
        'sh',
        '-c',
        get_best_python_sh(),
        '--',
        '-c',
        pyremote_build_bootstrap_source('omllm-agent'),
    )


@pytest.mark.asyncs('asyncio')
async def test_docker_remote_agent_start_error_includes_stderr(tmp_path):
    docker = tmp_path / 'docker'
    docker.write_text('#!/bin/sh\necho docker-broke >&2\nexit 41\n')
    docker.chmod(docker.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    connection = DockerRemoteAgentConnection(
        DockerContainerIdt('container-id'),
        DockerRemoteAgentConfig(
            docker=str(docker),
            startup_timeout_s=1.,
            shutdown_timeout_s=1.,
        ),
    )
    with pytest.raises(DockerRemoteAgentError) as exc_info:
        await connection.start()
    assert 'returncode=41' in str(exc_info.value)
    assert 'docker-broke' in str(exc_info.value)

    await connection.aclose()


##


# The target needs nothing but a Python 3.8+: no `om`, no dev image.
_LIVE_IMAGE = 'python:3.9-slim-trixie'


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
    # `docker run -d` returns before the container is fully up; exec'ing too early gives a transient "OCI runtime exec
    # failed". Probe with a trivial exec until it succeeds.
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if subprocess.run(['docker', 'exec', cid, 'true'], capture_output=True, check=False).returncode == 0:  # noqa
            return True
        time.sleep(0.1)
    return False


@pytest.mark.skipif(not _docker_daemon_up(), reason='no docker daemon')
@pytest.mark.asyncs('asyncio')
async def test_docker_remote_agent_live():
    # A throwaway container, the agent bootstrapped into it through the real `docker exec`, and both concerns driven.
    cid = subprocess.check_output([  # noqa: ASYNC221
        'docker',
        'run',
        '-d',
        '--rm',
        _LIVE_IMAGE,
        'sleep',
        'infinity',
    ]).decode().strip()
    try:
        if not _wait_container_ready(cid):
            pytest.skip('container did not become exec-ready')

        async with DockerRemoteAgentConnection(DockerContainerIdt(cid)) as connection:
            client = connection.client

            await client.fs.write_file('/root/remote.txt', b'from the host')
            assert (await client.fs.read_file('/root/remote.txt')).data == b'from the host'

            run = await client.processes.root.run(processes.ProcessSpec(
                ['sh', '-c', 'hostname; cat /root/remote.txt'],
                cwd='/root',
            ))
            assert run.returncode == 0
            hostname, content = run.stdout.decode().splitlines()
            # Docker's default hostname is the container's short id.
            assert cid.startswith(hostname)
            assert content == 'from the host'

            assert not client.processes.processes

    finally:
        subprocess.run(['docker', 'rm', '-f', cid], capture_output=True, check=False)  # noqa: ASYNC221
