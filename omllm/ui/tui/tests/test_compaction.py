"""The tui's own wiring of compaction, end to end but for the terminal: /compact through the injector to the store."""
import pytest

from omcore import check
from omcore import inject as inj

from .... import harness as har
from .... import llm
from ....agent.tests.scripted import text_message
from ..config import Config
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


@pytest.mark.asyncs('asyncio')
async def test_compact_command_through_the_tuis_wiring():
    seen: list = []

    def expect(invocation):
        seen.append(invocation.context)

    async with headless_tui(inj.override(
            bind_headless_tui(Config(model='scripted', immediate=True, in_memory=True)),
            bind_scripted_backend(
                text_message('hello'),
                text_message('The user said hi.'),
                llm.BackendScriptTurn(text_message('again'), expect=expect),
            ),
    )) as tui:
        await tui.session.prompt('hi')

        await tui.session.prompt('/compact')

        projection = check.not_none(tui.agent.state.context.projection)
        assert projection.summary == 'The user said hi.'
        assert projection.first_kept_message_index == 1
        assert len(tui.agent.state.context.messages or ()) == 2

        storage = await tui.injector[har.SessionStorage]
        assert [type(e) for e in await storage.get_entries()] == [
            har.MessageSessionEntry,
            har.MessageSessionEntry,
            har.ContextProjectionSessionEntry,
        ]

        await tui.session.prompt('and again')

        [llm_context] = seen
        assert [type(m) for m in llm_context.messages or []] == [llm.UserMessage, llm.AiMessage, llm.UserMessage]
        first = check.isinstance((llm_context.messages or [])[0], llm.UserMessage)
        assert check.isinstance(first.content, str).startswith('Earlier conversation summary:')
