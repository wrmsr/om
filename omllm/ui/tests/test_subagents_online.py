"""A real model, through the ui's injector, spawning an explorer in a child injector to read a directory it may not."""
import os.path
import tempfile

import pytest

from omcore import check
from omcore.secrets.tests.harness import HarnessSecrets

from ... import agent as agn
from ... import llm
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import headless_ui


##


_WORD = 'marmalade'


async def _test_explore(harness, model: str) -> None:
    dm = llm.default_models_by_name()[model]
    dm_sak = check.isinstance(check.not_none(dm.api_keys)[0], llm.SecretApiKey)
    harness[HarnessSecrets].get_or_skip(dm_sak.name)

    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        with open(os.path.join(td, 'quokka.txt'), 'w') as f:  # noqa: ASYNC230
            f.write(f'The secret word is {_WORD}.\n')

        async with headless_ui(bind_headless_ui(UiConfig(
                model=model,
                in_memory=True,
                fs=True,
                subagents=True,
                cwd=td,
                autoexec=[
                    '/permissions add allow subagent {}',
                    f'/permissions add allow glob_fs \'{{"glob":"{td}/**","modes":["r"]}}\'',
                ],
        ))) as hui:
            events: list = []
            hui.agent.subscribe(events.append)

            result = await hui.agent.prompt(
                'You must use the subagent tool for this, with its explore profile, and must not read any file '
                f'yourself. Have the subagent find the secret word written in the only .txt file in the directory {td} '
                'and report it back to you. Then reply with just that secret word, nothing else.',
            )

            assert result.reason is agn.AgentEndReason.COMPLETED, result.error

            # The parent spawned an explorer, which read with tools of its own, under the root's permission rules.
            assert [e.tool_name for e in events if isinstance(e, agn.ToolExecutionStartEvent)] == ['subagent']

            updates = [
                e.update
                for e in events
                if (
                    isinstance(e, agn.ToolExecutionUpdateEvent) and
                    isinstance(e.update, agn.SubagentEventToolProgressUpdate)
                )
            ]
            assert {u.profile for u in updates} == {'explore'}
            child_tools = [u.event.tool_name for u in updates if isinstance(u.event, agn.ToolExecutionStartEvent)]
            assert child_tools
            assert set(child_tools) <= {'read', 'ls', 'glob'}

            [tr] = [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]
            assert not tr.is_error
            assert _WORD in tr.content[0].text.lower()

            final = check.isinstance(result.new_messages[-1], llm.AiMessage)
            assert _WORD in ''.join(c.text for c in final.content if isinstance(c, llm.TextContent)).lower()


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(300)
async def test_live_explore_subagent_openai(harness):
    await _test_explore(harness, 'gpt-nano')


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.timeout(300)
async def test_live_explore_subagent_anthropic(harness):
    await _test_explore(harness, 'haiku')
