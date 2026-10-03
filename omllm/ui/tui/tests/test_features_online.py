import uuid

import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.secrets.tests.harness import HarnessSecrets

from .... import agent as agn
from .... import llm
from ..config import Config
from .features import write_verification_skill
from .headless import bind_headless_tui
from .headless import headless_tui


##


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.xdist_group('google-online')
@pytest.mark.parametrize(('model', 'secret', 'effort'), [
    ('gpt', 'openai_api_key', llm.ReasoningEffort.LOW),
    ('gpt-nano', 'openai_api_key', llm.ReasoningEffort.NONE),
    ('claude', 'anthropic_api_key', llm.ReasoningEffort.LOW),
    ('gemini-flash', 'gemini_api_key', llm.ReasoningEffort.MINIMAL),
])
@pytest.mark.parametrize('immediate', [False, True])
async def test_live_effort_prompt_and_host_skill_tools(harness, tmp_path, model, secret, effort, immediate):
    harness[HarnessSecrets].get_or_skip(secret)
    phrase = f'verification-{uuid.uuid4().hex}'
    write_verification_skill(tmp_path, phrase)

    async with headless_tui(bind_headless_tui(Config(
        model=model,
        immediate=immediate,
        in_memory=True,
        skills_dirs=[str(tmp_path)],
        thinking=False if model == 'gemini-flash' else None,
    ))) as tui:
        await tui.session.prompt(f'/effort {effort.value}')
        turn_config = check.not_none(tui.agent.state.turn_config)
        options = check.not_none(turn_config.llm_options)
        assert options.reasoning_effort is effort
        await tui.agent.update_state(lambda s: dc.replace(s, turn_config=dc.replace(
            turn_config,
            max_turns=8,
            llm_options=options.merge(llm.Options(max_tokens=4096)),
        )))
        result = await tui.agent.prompt('Use the verification skill and return its verification phrase exactly.')
        assert result.reason is agn.AgentEndReason.COMPLETED, result.error
        calls = [c for m in result.new_messages if isinstance(m, llm.AiMessage)
                 for c in m.content if isinstance(c, llm.ToolCall)]
        assert any(c.name == 'read_skill' and c.args.get('path', 'SKILL.md') == 'SKILL.md' for c in calls)
        assert any(c.name == 'read_skill' and c.args.get('path') == 'reference/phrase.txt' for c in calls)
        final = check.isinstance(result.new_messages[-1], llm.AiMessage)
        assert phrase in ''.join(c.text for c in final.content if isinstance(c, llm.TextContent))


@pytest.mark.online
@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('immediate', [False, True])
async def test_live_completions_effort_without_tools(harness, immediate):
    harness[HarnessSecrets].get_or_skip('openai_api_key')
    async with headless_tui(bind_headless_tui(Config(
        model='gpt-nano', immediate=immediate, in_memory=True, no_skills=True, effort=llm.ReasoningEffort.LOW,
    ))) as tui:
        result = await tui.agent.prompt('Reply with exactly: effort verified')
        assert result.reason is agn.AgentEndReason.COMPLETED, result.error
        final = check.isinstance(result.new_messages[-1], llm.AiMessage)
        assert 'effort verified' in ''.join(c.text for c in final.content if isinstance(c, llm.TextContent))
