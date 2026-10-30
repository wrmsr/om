import os.path
import tempfile

import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj

from ... import agent as agn
from ... import llm
from ...agent.tests.scripted import SCRIPTED_MODEL
from ...agent.tests.scripted import text_message
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import bind_scripted_backend
from .headless import headless_ui


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
    async with headless_ui(bind_headless_ui(UiConfig(
        model='scripted',
        immediate=True,
        in_memory=True,
        effort=llm.ReasoningEffort.LOW,
    ))) as hui:
        options = check.not_none(hui.agent.state.turn_config).llm_options
        assert options is not None
        assert options.reasoning_effort is llm.ReasoningEffort.LOW


@pytest.mark.asyncs('asyncio')
async def test_unsupported_effort_is_rejected_at_startup():
    # The plain scripted test model declares no effort levels at all.
    with pytest.raises(ValueError, match='does not support effort low'):
        async with headless_ui(inj.override(
            bind_headless_ui(UiConfig(
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
            bind_headless_ui(UiConfig(
                model='scripted',
                immediate=True,
                in_memory=True,
                effort=llm.ReasoningEffort.LOW,
                **kwargs,
            )),
            _bind_backend(model),
        )

    async with headless_ui(bind()) as hui:
        assert not hui.agent.state.context.tools

    with tempfile.TemporaryDirectory() as temp_dir:
        with pytest.raises(ValueError, match='does not support effort low with tools'):
            async with headless_ui(bind(fs=True, cwd=os.path.join(temp_dir, '.'))):
                pass
