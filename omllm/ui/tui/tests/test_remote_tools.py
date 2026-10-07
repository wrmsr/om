"""
The tui's container mode, end to end but for the terminal and the daemon: the remote agent bindings through the
injector, and tool calls through the agent into a (fake) container.
"""
import os
import shutil
import stat

import pytest

from omcore import check
from omcore import inject as inj

from .... import agent as agn
from .... import harness as har
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....core import processes
from ..config import Config
from ..types import TargetCwd
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


# Stands in for `docker exec -i <container> <cmd...>`: runs the command locally with the fake container's root as its
# working directory, which is where the remote agent then lives.
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


def _container_config() -> Config:
    return Config(
        model='scripted',
        immediate=True,
        in_memory=True,
        exec=True,
        fs=True,
        container='container-id',
    )


def _tool_results(tui, name: str) -> list[llm.ToolResultMessage]:
    return [
        m
        for m in (tui.agent.state.context.messages or [])
        if isinstance(m, llm.ToolResultMessage) and m.tool_name == name
    ]


async def _allow_everything_under(tui, cwd: str) -> None:
    # As `--yolo` does: the configured rules ask first and would win, so they go.
    await tui.commands.parse('permissions clear').run()
    await tui.commands.parse('permissions add allow exec {}').run()
    await tui.commands.parse(f'permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r","w"]}}\'').run()


##


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

    async with headless_tui(
            inj.override(
                bind_headless_tui(_container_config()),
                inj.bind(agn.DockerRemoteAgentConfig(docker=docker)),
            ),
    ) as tui:
        fs = await tui.injector[agn.FsOps]
        manager = await tui.injector[processes.ProcessManager]

        assert isinstance(fs, agn.RemoteFsOps)
        assert isinstance(manager, processes.RemoteProcessManager)
        assert (await tui.injector[TargetCwd]).v == cwd
        assert isinstance(await tui.injector[har.SessionStorage], har.InMemorySessionStorage)

        # The root scope is the remote manager's, and it is what the agent hands to tools.
        assert (await tui.injector[processes.RootProcessScope]) is manager.root
        assert check.not_none(tui.agent.state.tool_env).processes is manager.root

        # The host's platform sandbox cannot confine a process which runs in the container.
        ripgrep = await tui.injector[agn.RipgrepTool]
        assert not ripgrep._sandbox  # noqa: SLF001

        await fs.write_file(path, b'from remote')
        assert (await fs.read_file(path)).data == b'from remote'

        run = await manager.root.run(processes.ProcessSpec(
            ['sh', '-c', 'printf "%s:%s" "$PWD" "$MARKER"'],
            cwd=cwd,
            env={'MARKER': 'inside'},
        ))
        assert run.returncode == 0
        assert run.stdout == f'{cwd}:inside'.encode()


@pytest.mark.asyncs('asyncio')
async def test_bash_tool_runs_in_the_container_through_the_agent(tmp_path):
    docker = _make_fake_docker(tmp_path)
    cwd = os.path.realpath(tmp_path / 'container-root')

    async with headless_tui(inj.override(
            bind_headless_tui(_container_config()),
            inj.bind(agn.DockerRemoteAgentConfig(docker=docker)),
            bind_scripted_backend(
                tool_call_message(llm.ToolCall(
                    id='t1',
                    name='bash',
                    args={'command': 'printf "%s:remote-ok\n" "$PWD"; echo warn >&2; exit 5'},
                )),
                text_message('done'),
            ),
    )) as tui:
        tool_env = check.not_none(tui.agent.state.tool_env)
        assert tool_env.cwd == cwd

        await _allow_everything_under(tui, cwd)
        await tui.agent.prompt('run it')

        # The command ran in the container's working directory, and its stderr and exit code came back framed.
        [result] = _tool_results(tui, 'bash')
        text = check.isinstance(result.content[0], llm.TextContent).text
        assert f'{cwd}:remote-ok' in text
        assert 'warn' in text
        assert 'exit code 5' in text

        manager = await tui.injector[processes.ProcessManager]
        assert not manager.processes


@pytest.mark.skipif(not shutil.which('rg'), reason='no rg')
@pytest.mark.asyncs('asyncio')
async def test_ripgrep_tool_runs_in_the_container_through_the_agent(tmp_path):
    docker = _make_fake_docker(tmp_path)
    cwd = os.path.realpath(tmp_path / 'container-root')
    (tmp_path / 'container-root' / 'haystack.txt').write_text('hay\nneedle here\n')

    async with headless_tui(inj.override(
            bind_headless_tui(_container_config()),
            inj.bind(agn.DockerRemoteAgentConfig(docker=docker)),
            bind_scripted_backend(
                tool_call_message(llm.ToolCall(
                    id='t1',
                    name='ripgrep',
                    args={'args': ['needle']},
                )),
                text_message('done'),
            ),
    )) as tui:
        await _allow_everything_under(tui, cwd)
        await tui.agent.prompt('search')

        [result] = _tool_results(tui, 'ripgrep')
        text = check.isinstance(result.content[0], llm.TextContent).text
        assert 'needle here' in text
