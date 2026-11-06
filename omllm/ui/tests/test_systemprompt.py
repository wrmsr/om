import pytest

from omcore import check

from ..agent.systemprompt import DEFAULT_SYSTEM_PROMPT
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import headless_ui


##


_CWD_LINE = 'Current working directory: '


def _config(**kwargs):
    return UiConfig(
        model='scripted',
        immediate=True,
        in_memory=True,
        **kwargs,
    )


@pytest.mark.asyncs('asyncio')
async def test_default_system_prompt():
    async with headless_ui(bind_headless_ui(_config())) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert prompt.startswith(DEFAULT_SYSTEM_PROMPT)
        assert _CWD_LINE in prompt


@pytest.mark.asyncs('asyncio')
async def test_system_prompt_override():
    async with headless_ui(bind_headless_ui(_config(system_prompt='You are a pirate.'))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert prompt.startswith('You are a pirate.')
        assert DEFAULT_SYSTEM_PROMPT not in prompt
        assert _CWD_LINE in prompt


@pytest.mark.asyncs('asyncio')
async def test_empty_system_prompt_override():
    async with headless_ui(bind_headless_ui(_config(system_prompt=''))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert DEFAULT_SYSTEM_PROMPT not in prompt
        assert prompt.startswith(_CWD_LINE)


@pytest.mark.asyncs('asyncio')
async def test_extra_system_prompt():
    async with headless_ui(bind_headless_ui(_config(extra_system_prompt='Reply in haiku.'))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)

        mission_at = prompt.index(DEFAULT_SYSTEM_PROMPT)
        extra_at = prompt.index('Reply in haiku.')
        cwd_at = prompt.index(_CWD_LINE)

        assert mission_at == 0
        assert mission_at < extra_at < cwd_at


@pytest.mark.asyncs('asyncio')
async def test_override_and_extra_system_prompt():
    async with headless_ui(bind_headless_ui(_config(
        system_prompt='You are a pirate.',
        extra_system_prompt='Reply in haiku.',
    ))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert prompt.startswith('You are a pirate.\n\nReply in haiku.\n\n' + _CWD_LINE)


def test_system_prompt_arguments():
    config = UiConfig.parse_from_arguments([
        '--system-prompt', 'You are a pirate.',
        '--extra-system-prompt', 'Reply in haiku.',
    ])
    assert config.system_prompt == 'You are a pirate.'
    assert config.extra_system_prompt == 'Reply in haiku.'

    assert UiConfig.parse_from_arguments([]).system_prompt is None
    assert UiConfig.parse_from_arguments(['--system-prompt', '']).system_prompt == ''
