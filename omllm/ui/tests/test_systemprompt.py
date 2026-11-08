import os.path

import pytest

from omcore import check

from ..agent.systemprompt import DEFAULT_SYSTEM_PROMPT
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import headless_ui


##


_ENVIRONMENT_HEADER = 'Environment at startup:'
_CWD_LINE = '- Working directory: '


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
        assert _ENVIRONMENT_HEADER in prompt

        # The directory the prompt names is the one the tools get.
        cwd = check.not_none(check.not_none(hui.agent.state.tool_env).cwd)
        assert cwd == os.path.realpath(os.getcwd())
        assert f'{_CWD_LINE}{cwd}\n' in prompt


@pytest.mark.asyncs('asyncio')
async def test_system_prompt_override():
    async with headless_ui(bind_headless_ui(_config(system_prompt='You are a pirate.'))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert prompt.startswith('You are a pirate.')
        assert DEFAULT_SYSTEM_PROMPT not in prompt
        assert _ENVIRONMENT_HEADER in prompt


@pytest.mark.asyncs('asyncio')
async def test_empty_system_prompt_override():
    async with headless_ui(bind_headless_ui(_config(system_prompt=''))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert DEFAULT_SYSTEM_PROMPT not in prompt
        assert prompt.startswith(_ENVIRONMENT_HEADER)


@pytest.mark.asyncs('asyncio')
async def test_extra_system_prompt():
    async with headless_ui(bind_headless_ui(_config(extra_system_prompt='Reply in haiku.'))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)

        mission_at = prompt.index(DEFAULT_SYSTEM_PROMPT)
        extra_at = prompt.index('Reply in haiku.')
        environment_at = prompt.index(_ENVIRONMENT_HEADER)

        assert mission_at == 0
        assert mission_at < extra_at < environment_at


@pytest.mark.asyncs('asyncio')
async def test_override_and_extra_system_prompt():
    async with headless_ui(bind_headless_ui(_config(
        system_prompt='You are a pirate.',
        extra_system_prompt='Reply in haiku.',
    ))) as hui:
        prompt = check.not_none(hui.agent.state.context.system_prompt)
        assert prompt.startswith('You are a pirate.\n\nReply in haiku.\n\n' + _ENVIRONMENT_HEADER)


@pytest.mark.asyncs('asyncio')
async def test_requested_cwd_is_resolved_at_setup(tmp_path):
    root = os.path.realpath(tmp_path)
    real = os.path.join(root, 'real')
    os.mkdir(real)
    link = os.path.join(root, 'link')
    os.symlink(real, link)

    async with headless_ui(bind_headless_ui(_config(cwd=link))) as hui:
        assert check.not_none(hui.agent.state.tool_env).cwd == real
        assert f'{_CWD_LINE}{real}\n' in check.not_none(hui.agent.state.context.system_prompt)


@pytest.mark.asyncs('asyncio')
async def test_a_bad_cwd_fails_setup(tmp_path):
    with pytest.raises(FileNotFoundError):
        async with headless_ui(bind_headless_ui(_config(cwd=os.path.join(os.path.realpath(tmp_path), 'missing')))):
            pass


def test_system_prompt_arguments():
    config = UiConfig.parse_from_arguments([
        '--system-prompt', 'You are a pirate.',
        '--extra-system-prompt', 'Reply in haiku.',
    ])
    assert config.system_prompt == 'You are a pirate.'
    assert config.extra_system_prompt == 'Reply in haiku.'

    assert UiConfig.parse_from_arguments([]).system_prompt is None
    assert UiConfig.parse_from_arguments(['--system-prompt', '']).system_prompt == ''
