import os.path

import pytest

from omcore import lang

from ... import agent as agn
from ...core import ui
from ..config import UiConfig
from ..paths import AgentCwdDisplayPathResolver
from ..paths import get_agent_cwd
from .headless import bind_headless_ui
from .headless import headless_ui


class _NoTurnRunner(agn.TurnRunner):
    async def run_turn(self, params: agn.TurnParams) -> agn.TurnResult:
        raise NotImplementedError


def test_display_paths_follow_the_agents_state():
    agent = agn.Agent(
        backends=agn.DictBackendManager({}),
        turn_runner=_NoTurnRunner(),
    )
    options = ui.TextRenderingOptions(paths=AgentCwdDisplayPathResolver(agent))

    # Nothing is known of the directory until the agent is set up: paths are as given.
    assert get_agent_cwd(agent) is None
    assert ui.resolve_display_path(options, '/w/a/b.py') == '/w/a/b.py'

    lang.sync_await(agent.update_state(lambda s: agn.State(context=s.context, tool_env=agn.ToolEnvironment(cwd='/w'))))

    assert get_agent_cwd(agent) == '/w'
    assert ui.resolve_display_path(options, '/w/a/b.py') == 'a/b.py'
    assert ui.resolve_display_path(options, '/elsewhere/b.py') == '/elsewhere/b.py'


@pytest.mark.asyncs('asyncio')
async def test_the_ui_shows_paths_relative_to_the_resolved_cwd(tmp_path):
    root = os.path.realpath(tmp_path)

    async with headless_ui(bind_headless_ui(UiConfig(
        model='scripted',
        immediate=True,
        in_memory=True,
        cwd=root,
    ))) as hui:
        options = ui.TextRenderingOptions(paths=AgentCwdDisplayPathResolver(hui.agent))
        assert ui.resolve_display_path(options, os.path.join(root, 'a', 'b.py')) == os.path.join('a', 'b.py')
