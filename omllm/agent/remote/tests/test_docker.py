import stat

import pytest

from omcore.os.pyremote.bestpython import get_best_python_sh
from omcore.os.pyremote.core import pyremote_build_bootstrap_source

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
