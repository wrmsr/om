import os
import stat

import pytest

from omcore import inject as inj

from .... import agent as agn
from .... import harness as har
from ....core import processes
from ..config import Config
from ..config import TargetCwd
from .headless import bind_headless_tui
from .headless import headless_tui


_FAKE_DOCKER = r"""#!/bin/sh
set -eu
[ "$1" = exec ] || { echo "fake-docker: expected exec, got $1" >&2; exit 2; }
shift
while [ "$#" -gt 0 ]; do
  case "$1" in
    -i) shift ;;
    -*) echo "fake-docker: unexpected option $1" >&2; exit 2 ;;
    *) shift; break ;;
  esac
done
cd "$(dirname "$0")/container-root"
exec "$@"
"""


def _make_fake_docker(tmp_path) -> str:
    path = tmp_path / 'docker'
    (tmp_path / 'container-root').mkdir()
    path.write_text(_FAKE_DOCKER)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(path)


def test_container_arguments():
    config = Config.parse_from_arguments([
        '--container', 'container-id',
        '--cwd', '/workspace',
        '--exec',
        '--fs',
    ])
    assert config.container == 'container-id'
    assert config.cwd == '/workspace'
    assert config.exec
    assert config.fs


@pytest.mark.asyncs('asyncio')
async def test_docker_remote_tool_bindings(tmp_path):
    docker = _make_fake_docker(tmp_path)
    cwd = os.path.realpath(tmp_path / 'container-root')
    path = os.path.join(cwd, 'remote.txt')

    config = Config(
        model='scripted',
        immediate=True,
        in_memory=True,
        exec=True,
        fs=True,
        container='container-id',
    )

    async with headless_tui(
            inj.override(
                bind_headless_tui(config),
                inj.bind(agn.DockerRemoteAgentConfig(docker=docker)),
            ),
    ) as tui:
        fs = await tui.injector[agn.FsOps]
        manager = await tui.injector[processes.ProcessManager]

        assert isinstance(fs, agn.RemoteFsOps)
        assert isinstance(manager, agn.RemoteProcessManager)
        assert (await tui.injector[TargetCwd]).v == cwd
        assert isinstance(await tui.injector[har.SessionStorage], har.InMemorySessionStorage)

        await fs.write_file(path, b'from remote')
        assert (await fs.read_file(path)).data == b'from remote'

        run = await manager.root.run(processes.ProcessSpec(
            ['sh', '-c', 'printf "%s:%s" "$PWD" "$MARKER"'],
            cwd=cwd,
            env={'MARKER': 'inside'},
        ))
        assert run.returncode == 0
        assert run.stdout == f'{cwd}:inside'.encode()
