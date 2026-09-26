import asyncio

import pytest

from omcore import check
from omcore import inject as inj

from ..... import agent as agn
from ..... import harness as har
from ..... import llm
from .....agent.tests.scripted import scripted_backend
from .....agent.tests.scripted import text_message
from .....core import ui
from ...config import Config
from ...tests.features import RecordingTextDisplayer
from ...tests.headless import bind_headless_tui
from ...tests.headless import headless_tui
from ..output import AgentEventRenderer
from ..promptpump import PromptPump
from .utils import make_app
from .utils import settle


##


@pytest.mark.asyncs('asyncio')
async def test_steer_reaches_running_prompt_ahead_of_queued_input():
    started = asyncio.Event()
    release = asyncio.Event()
    seen = []

    async def gate(point):
        if point.invocation_index == 0 and point.emission_index == 0:
            started.set()
            await release.wait()

    backend = scripted_backend(*[
        llm.BackendScriptTurn(text_message(text), expect=lambda inv: seen.append(inv.context))
        for text in ['first', 'steered', 'followup']
    ], stream=True, gate=gate)
    display = RecordingTextDisplayer()
    config = Config(model='scripted', in_memory=True, no_skills=True)
    async with headless_tui(inj.override(
        bind_headless_tui(config),
        inj.bind(ui.TextDisplayer, to_const=display),
        inj.bind(agn.BackendManager, to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        })),
    )) as tui:
        app, _ = make_app()
        renderer = AgentEventRenderer(app=app, text_displayer=display, config=config)
        tui.agent.subscribe(renderer.on_agent_event)
        commands = await tui.injector[har.CommandsManager]
        pump = PromptPump(session=tui.session, app=app, commands=commands)
        try:
            pump.submit('initial')
            await started.wait()
            pump.submit('queued followup')
            pump.submit('/steer "new direction"')
            await display.displayed.wait()
            assert display.lines[-1] == 'Steering queued for the next turn boundary.'
            assert app.is_busy
            assert len(seen) == 1
            release.set()
            await settle(lambda: len(seen) == 3 and not tui.agent.is_running, max_steps=200)
            assert len(seen) == 3
            assert 'new direction' in str(seen[1].messages)
            assert 'queued followup' not in str(seen[1].messages)
            assert 'queued followup' in str(seen[2].messages)
            messages = check.not_none(tui.agent.state.context.messages)
            assert 'steer' not in [m.content for m in messages if isinstance(m, llm.UserMessage)]
        finally:
            release.set()
            await pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_idle_steering_does_not_leak_into_a_later_prompt():
    display = RecordingTextDisplayer()
    async with headless_tui(inj.override(
        bind_headless_tui(Config(model='scripted', in_memory=True, no_skills=True)),
        inj.bind(ui.TextDisplayer, to_const=display),
    )) as tui:
        await tui.session.prompt('/steer stray')
        assert 'No prompt is running' in display.lines[-1]
        await tui.session.prompt('hello')
        assert 'stray' not in str(tui.agent.state.context.messages)


@pytest.mark.asyncs('asyncio')
async def test_steer_rejects_exclusive_updates_and_terminal_delivery():
    display = RecordingTextDisplayer()
    async with headless_tui(inj.override(
        bind_headless_tui(Config(model='scripted', in_memory=True, no_skills=True)),
        inj.bind(ui.TextDisplayer, to_const=display),
    )) as tui:
        async def update(state):
            assert tui.agent.is_running and not tui.agent.is_prompting
            await tui.session.prompt('/steer during-update')
            return state

        await tui.agent.update_state_exclusively(update)
        assert 'No prompt is running' in display.lines[-1]

        async def on_event(event):
            if isinstance(event, agn.AgentEndEvent):
                assert tui.agent.is_running and not tui.agent.is_prompting
                await tui.session.prompt('/steer during-terminal-event')

        tui.agent.subscribe(on_event)
        await tui.session.prompt('first')
        assert 'No prompt is running' in display.lines[-1]
        await tui.session.prompt('second')
        assert 'during-update' not in str(tui.agent.state.context.messages)
        assert 'during-terminal-event' not in str(tui.agent.state.context.messages)


@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('start_command', [False, True])
async def test_shutdown_owns_immediate_command_tasks(start_command):
    started = asyncio.Event()
    stopped = asyncio.Event()

    class BlockingDisplay(RecordingTextDisplayer):
        async def display_text(self, *texts):
            self.displayed.set()
            try:
                await asyncio.Event().wait()
            finally:
                # Closing the pump must cancel the prompt before joining this command.
                await stopped.wait()

    async def gate(point):
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    backend = scripted_backend(text_message('blocked'), stream=True, gate=gate)
    display = BlockingDisplay()
    async with headless_tui(inj.override(
        bind_headless_tui(Config(model='scripted', in_memory=True, no_skills=True)),
        inj.bind(ui.TextDisplayer, to_const=display),
        inj.bind(agn.BackendManager, to_const=agn.DictBackendManager({
            llm.ImmediateBackend: {None: backend},  # type: ignore[type-abstract]
        })),
    )) as tui:
        app, _ = make_app()
        pump = PromptPump(session=tui.session, app=app, commands=await tui.injector[har.CommandsManager])
        try:
            pump.submit('initial')
            await started.wait()
            pump.submit('/steer correction')
            tasks = list(pump._command_tasks)  # noqa: SLF001
            assert len(tasks) == 1
            if start_command:
                await display.displayed.wait()
        finally:
            await pump.aclose()
        assert stopped.is_set()
        assert all(t.cancelled() for t in tasks)
        assert not pump._command_tasks  # noqa: SLF001
        assert not tui.agent.is_running
