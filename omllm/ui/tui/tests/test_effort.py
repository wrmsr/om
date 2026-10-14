import os.path
import tempfile

import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import SCRIPTED_MODEL
from ....agent.tests.scripted import text_message
from ..config import Config
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


def _bind_backend(model: llm.Model) -> inj.Elemental:
    return inj.bind(
        agn.BackendManager,
        to_const=agn.DictBackendManager.of(llm.ScriptedImmediateBackend(
            model,
            llm.BackendScript([llm.BackendScriptTurn(text_message('hello'))]),
        )),
    )


@pytest.mark.asyncs('asyncio')
async def test_effort_reaches_turn_options():
    async with headless_tui(bind_headless_tui(Config(
        model='scripted',
        immediate=True,
        in_memory=True,
        effort=llm.ReasoningEffort.LOW,
    ))) as tui:
        options = check.not_none(tui.agent.state.turn_config).llm_options
        assert options is not None
        assert options.reasoning_effort is llm.ReasoningEffort.LOW


@pytest.mark.asyncs('asyncio')
async def test_unsupported_effort_is_rejected_at_startup():
    # The plain scripted test model declares no effort levels at all.
    with pytest.raises(ValueError, match='does not support effort low'):
        async with headless_tui(inj.override(
            bind_headless_tui(Config(
                model='scripted',
                immediate=True,
                in_memory=True,
                effort=llm.ReasoningEffort.LOW,
            )),
            bind_scripted_backend(text_message('hello')),
        )):
            pass


@pytest.mark.asyncs('asyncio')
async def test_effort_is_validated_against_installed_tools():
    model = dc.replace(
        SCRIPTED_MODEL,
        reasoning_efforts=frozenset({llm.ReasoningEffort.LOW}),
        reasoning_efforts_with_tools=frozenset(),
    )

    def bind(**kwargs):
        return inj.override(
            bind_headless_tui(Config(
                model='scripted',
                immediate=True,
                in_memory=True,
                effort=llm.ReasoningEffort.LOW,
                **kwargs,
            )),
            _bind_backend(model),
        )

    async with headless_tui(bind()) as tui:
        assert not tui.agent.state.context.tools

    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match='does not support effort low with tools'):
            async with headless_tui(bind(fs=True, cwd=os.path.join(temp_dir, '.'))):
                pass
