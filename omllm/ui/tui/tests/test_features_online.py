import pytest

from omcore import check
from omcore.secrets.tests.harness import HarnessSecrets

from .... import agent as agn
from .... import llm
from ..config import Config
from .headless import bind_headless_tui
from .headless import headless_tui


##


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('immediate', [False, True])
async def test_live_completions_effort_without_tools(harness, immediate):
    harness[HarnessSecrets].get_or_skip('openai_api_key')
    async with headless_tui(bind_headless_tui(Config(
        model='gpt-nano',
            immediate=immediate,
            in_memory=True,
            effort=llm.ReasoningEffort.LOW,
    ))) as tui:
        result = await tui.agent.prompt('Reply with exactly: effort verified')
        assert result.reason is agn.AgentEndReason.COMPLETED, result.error
        final = check.isinstance(result.new_messages[-1], llm.AiMessage)
        assert 'effort verified' in ''.join(c.text for c in final.content if isinstance(c, llm.TextContent))
