"""The ui's own wiring of compaction, end to end but for the terminal: /compact through the injector to the store."""
import pytest

from omcore import check
from omcore import inject as inj

from ... import agent as agn
from ... import llm
from ...agent.tests.scripted import text_message
from ..config import UiConfig
from .headless import bind_headless_ui
from .headless import bind_scripted_backend
from .headless import headless_ui


##


@pytest.mark.asyncs('asyncio')
async def test_compact_command_through_the_uis_wiring():
    seen: list = []

    def expect(invocation):
        seen.append(invocation.context)

    async with headless_ui(inj.override(
            bind_headless_ui(UiConfig(
                model='scripted',
                immediate=True,
                in_memory=True,
            )),
            bind_scripted_backend(
                text_message('hello'),
                text_message('The user said hi.'),
                llm.BackendScriptTurn(text_message('again'), expect=expect),
            ),
    )) as hui:
        await hui.agent.prompt('hi')

        await hui.commands.parse('compact').run()

        projection = check.not_none(hui.agent.state.context.projection)
        assert projection.summary == 'The user said hi.'
        assert projection.first_kept_message_index == 1
        assert len(hui.agent.state.context.messages or ()) == 2

        storage = await hui.injector[agn.SessionStorage]
        assert [type(e) for e in await storage.get_entries()] == [
            agn.MessageSessionEntry,
            agn.MessageSessionEntry,
            agn.ContextProjectionSessionEntry,
        ]

        await hui.agent.prompt('and again')

        [llm_context] = seen
        assert [type(m) for m in llm_context.messages or []] == [llm.UserMessage, llm.AiMessage, llm.UserMessage]
        first = check.isinstance((llm_context.messages or [])[0], llm.UserMessage)
        assert check.isinstance(first.content, str).startswith('Earlier conversation summary:')
