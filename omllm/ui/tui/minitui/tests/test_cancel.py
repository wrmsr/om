"""
The cancel path, hop by hop and end to end: ctrl+q -> `PromptPump.cancel_current` -> task cancellation -> the turn
loop's `AgentEndEvent(CANCELLED)` -> `AgentEventRenderer` -> `MinituiChatApp.abort_ai_turn`.
"""
import asyncio
import typing as ta

import pytest

from omdev.tui import minitui as mt

from ..... import agent as agn
from ..... import harness as har
from ..... import llm
from .....agent.eval.permissions import EvalLanguage
from .....agent.eval.permissions import EvalPermissionTarget
from ...config import Config
from ..app import AppKey
from ..app import MinituiChatApp
from ..input import CardPermissionAsker
from ..main import AppQuitSignal
from ..main import PromptPump
from ..main import Shutdown
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from .utils import BlockingSession
from .utils import Driver
from .utils import FailingSession
from .utils import RecordingSession
from .utils import app_key
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app
from .utils import settle


##
# App-level abort


def test_abort_mid_stream_settles_tail_and_resets_state():
    app, driver = make_app()

    app.begin_ai_turn()
    app.set_thinking(True)
    app.set_thinking(False)
    app.stream_feed('Hello **wor')
    assert any('Hello' in line for line in frame_lines(app))
    driver.commits.clear()

    app.abort_ai_turn(cancelled=True)

    committed = commit_texts(driver)
    assert any('Hello' in c and 'wor' in c for c in committed)
    assert committed[-1] == '× cancelled\n'
    lines = frame_lines(app)
    assert not any('Hello' in line for line in lines)
    assert not app.is_busy
    assert any(' idle ' in line for line in lines)

    # A fresh stream cycle starts clean after the aborted one.
    app.begin_ai_turn()
    app.stream_feed('Again')
    assert any('Again' in line and 'Hello' not in line for line in frame_lines(app))


def test_abort_while_thinking_resets_status_and_stops_spinner():
    app, driver = make_app()

    app.begin_ai_turn()
    app.set_thinking(True)
    assert any(' thinking ' in line for line in frame_lines(app))
    before = driver.invalidations
    driver.fire_after(.1)
    assert driver.invalidations > before

    app.abort_ai_turn(cancelled=True)

    # The open `ai` block is closed visibly even though nothing streamed.
    assert commit_texts(driver) == ['ai', '× cancelled\n']
    assert not app.is_busy
    assert any(' idle ' in line for line in frame_lines(app))
    before = driver.invalidations
    driver.fire_after(.1)
    assert driver.invalidations == before


def test_turn_start_refreshes_status_immediately():
    app, _ = make_app()
    assert any(' idle ' in line for line in frame_lines(app))

    app.begin_ai_turn()

    assert any(' streaming ' in line for line in frame_lines(app))


def test_abort_when_idle_commits_nothing():
    app, driver = make_app()

    app.abort_ai_turn(cancelled=True)
    app.abort_ai_turn(cancelled=False)

    assert driver.commits == []
    assert not app.is_busy


def test_new_turn_after_abort_is_unaffected_by_stale_finalize_timers():
    app, driver = make_app()

    app.begin_ai_turn()
    app.tool_started('call-a', 'alpha', ())
    app.tool_finished('call-a', 'alpha', ok=True)
    app.tool_started('call-b', 'beta', ())
    app.abort_ai_turn(cancelled=True)
    assert len(driver.commits) >= 2

    # The next turn reuses the same call ids (scripted or replayed models do) before the old finalize timer fires.
    app.begin_ai_turn()
    app.tool_started('call-a', 'alpha', ())
    app.tool_started('call-b', 'beta', ())
    driver.commits.clear()

    driver.fire_after(1.)

    assert driver.commits == []
    lines = frame_lines(app)
    assert any('alpha  running...' in line for line in lines)
    assert any('beta  running...' in line for line in lines)


def test_reactivated_card_survives_its_stale_finalize_timer():
    app, driver = make_app()

    # The key comes back to life before the finalize scheduled by its earlier completion fires.
    app.tool_started('call-a', 'alpha', ())
    app.tool_finished('call-a', 'alpha', ok=True)
    app.tool_started('call-a', 'alpha', ())
    driver.fire_after(.8)
    assert driver.commits == []
    assert any('alpha  running...' in line for line in frame_lines(app))

    # Likewise a denial's finalize must not race the failure result that follows it.
    app.begin_permission_card('call-a', 'alpha', (), lambda allowed: None)
    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    app.tool_finished('call-a', 'alpha', ok=False)
    driver.fire_after(.6)
    assert driver.commits == []
    driver.fire_after(.3)
    assert len(driver.commits) == 1
    assert 'alpha  failed' in commit_texts(driver)[0]


def test_cancel_key_when_idle_falls_through_harmlessly():
    app, driver = make_app()
    app.on_cancel = lambda: False

    app.handle_event(mt.KeyEvent(mt.Key('a'), text='a'))
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))

    assert app.render(80, 24).lines
    assert driver.commits == []
    assert not driver.stopped


def test_queued_ask_whose_card_vanished_is_re_presented():
    app, _ = make_app()
    responses = []
    cancellations = []

    app.tool_started('call-a', 'alpha', ())
    app.tool_started('call-b', 'beta', ())
    app.begin_permission_card('call-b', 'beta', (), lambda allowed: responses.append(('call-b', allowed)))
    app.begin_permission_card(
        'call-a',
        'alpha',
        [[mt.Segment('target: a')]],
        lambda allowed: responses.append(('call-a', allowed)),
        on_cancel=lambda: cancellations.append('call-a'),
    )

    # No public path drops a card out from under a queued ask any more (finalize timers are cancelled on reactivation);
    # this is the safety net should one ever appear. The ask is a tool parked mid-execution, not display: it must be
    # presented, not withdrawn as a cancellation.
    app._cards.pop('call-a')  # noqa: SLF001
    assert not any('alpha' in line for line in frame_lines(app))

    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_ALLOW)))

    assert responses == [('call-b', True)]
    assert cancellations == []
    assert any('alpha  awaiting confirmation' in line for line in frame_lines(app))

    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    assert responses == [('call-b', True), ('call-a', False)]


##
# The asker


async def _unused_executor(ctx):
    raise AssertionError


def _ask(asker, call_id, name):
    context = agn.ToolContext(
        tool=agn.Tool(llm_tool=llm.Tool(name=name), executor=_unused_executor),
        args={},
        llm_tool_call=llm.ToolCall(call_id, name, {}),
    )
    return asyncio.get_running_loop().create_task(asker.ask(
        agn.PermissionRequestor(tool_context=context),
        EvalPermissionTarget(language=EvalLanguage.JS, code='1 + 1'),
        agn.PermissionRule(agn.EvalPermissionMatcher(), agn.PermissionState.ASK),
    ))


def _shows(app, text):
    return lambda: any(text in line for line in frame_lines(app))


@pytest.mark.asyncs('asyncio')
async def test_asker_resolves_through_card_keys():
    app, _ = make_app()
    asker = CardPermissionAsker(app=app)

    app.tool_started('call-a', 'alpha', ())
    allow_task = _ask(asker, 'call-a', 'alpha')
    await settle(_shows(app, 'alpha  awaiting confirmation'))
    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_ALLOW)))
    assert await allow_task is agn.PermissionState.ALLOW
    assert any('alpha  running...' in line for line in frame_lines(app))

    app.tool_started('call-b', 'beta', ())
    deny_task = _ask(asker, 'call-b', 'beta')
    await settle(_shows(app, 'beta  awaiting confirmation'))
    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    assert await deny_task is agn.PermissionState.DENY
    assert any('beta  denied' in line for line in frame_lines(app))


@pytest.mark.asyncs('asyncio')
async def test_asker_task_cancel_unwinds_and_abort_finalizes_card():
    app, driver = make_app()
    asker = CardPermissionAsker(app=app)

    app.begin_ai_turn()
    app.tool_started('call-a', 'alpha', ())
    task = _ask(asker, 'call-a', 'alpha')
    await settle(_shows(app, 'alpha  awaiting confirmation'))
    driver.commits.clear()

    # Cancelling the prompt task cancels the future the ask is parked on; the tool executor unwinds...
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # ...and the turn loop's terminal event lands here.
    app.abort_ai_turn(cancelled=True)

    committed = commit_texts(driver)
    assert any('alpha  cancelled' in c for c in committed)
    assert not any('alpha' in line for line in frame_lines(app))

    # Nothing is left to confirm: the bindings are inert and no callback fires into the dead request.
    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_ALLOW)))
    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    assert commit_texts(driver) == committed


@pytest.mark.asyncs('asyncio')
async def test_abort_cancels_active_and_queued_asks():
    app, _ = make_app()
    asker = CardPermissionAsker(app=app)

    app.begin_ai_turn()
    app.tool_started('call-a', 'alpha', ())
    app.tool_started('call-b', 'beta', ())
    tasks = [_ask(asker, 'call-a', 'alpha'), _ask(asker, 'call-b', 'beta')]
    await settle(_shows(app, 'beta  queued for confirmation'))

    app.abort_ai_turn(cancelled=False)

    for task in tasks:
        with pytest.raises(asyncio.CancelledError):
            await task
    assert not any(title in line for title in ('alpha', 'beta') for line in frame_lines(app))


##
# The pump


@pytest.mark.asyncs('asyncio')
async def test_failed_prompt_displays_error_and_runs_next():
    app, driver = make_app()
    session = FailingSession(RuntimeError('boom'))
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)

    pump.submit('first')
    pump.submit('second')
    await session.second_done.wait()

    assert session.prompts == ['first', 'second']
    assert any('error: RuntimeError' in c for c in commit_texts(driver))
    await pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_cancel_before_prompt_task_starts_does_not_wedge_pump():
    app, _ = make_app()
    session = RecordingSession()
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)
    app.on_cancel = pump.cancel_current

    # Enter then ctrl+q arriving in one input read: dispatched back to back before the loop turns.
    pump.submit('first')
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    pump.submit('second')

    await settle(lambda: 'second' in session.prompts)

    assert session.prompts == ['second']
    assert not pump.cancel_current()
    await pump.aclose()


##
# End to end through a real turn loop


class _BlockingTool:
    def __init__(self) -> None:
        super().__init__()

        self.started = asyncio.Event()
        self._never = asyncio.Event()

    async def execute(self, ctx):
        self.started.set()
        await self._never.wait()
        raise AssertionError

    def tool(self):
        return agn.Tool(llm_tool=llm.Tool(name='block'), executor=self.execute)


class _BlockingBackend(llm.ImmediateBackend):
    def __init__(self) -> None:
        super().__init__()

        self._model = llm.Model(key=llm.ModelKey('test', 'blocking'), backend='test')
        self.started = asyncio.Event()
        self._never = asyncio.Event()

    @property
    def model(self):
        return self._model

    async def immediate(self, context, options=None):
        self.started.set()
        await self._never.wait()
        raise AssertionError


def _tool_call_backend(call_id, name):
    model = llm.Model(key=llm.ModelKey('scripted', 'test'), backend='scripted')
    return llm.ScriptedImmediateBackend(model, llm.BackendScript([
        llm.BackendScriptTurn(llm.AiMessage(
            [llm.ToolCall(id=call_id, name=name, args={})],
            stop_reason='tool_use',
        )),
    ]))


class _TurnLoopSession:
    """Runs a real TurnLoop per prompt so a cancel unwinds the actual agent path into the renderer."""

    def __init__(self, *, backend, tools, subscriber) -> None:
        super().__init__()

        self._backend = backend
        self._tools = tools
        self._subscriber = subscriber

        self.finished = asyncio.Event()

    async def prompt(self, text):
        loop = agn.TurnLoop(
            new_messages=[llm.UserMessage(text)],
            context=agn.Context(tools=agn.ToolSet(list(self._tools))),
            subscriber=self._subscriber,
            llm_backend=self._backend,
        )
        try:
            await loop.run()
        finally:
            self.finished.set()


def _wire(app, session):
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)
    app.on_submit = pump.submit
    app.on_cancel = pump.cancel_current
    return pump


@pytest.mark.asyncs('asyncio')
async def test_cancel_key_unwinds_running_tool_into_cancelled_card():
    app, driver = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())
    tool = _BlockingTool()
    session = _TurnLoopSession(
        backend=_tool_call_backend('t1', 'block'),
        tools=[tool.tool()],
        subscriber=renderer.on_agent_event,
    )
    pump = _wire(app, session)

    pump.submit('go')
    await tool.started.wait()
    lines = frame_lines(app)
    assert any(' streaming ' in line for line in lines)
    assert any('block  running...' in line for line in lines)
    driver.commits.clear()

    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    await session.finished.wait()

    assert not app.is_busy
    committed = commit_texts(driver)
    assert any('block  cancelled' in c for c in committed)
    assert committed[-1] == '× cancelled\n'
    assert not any('block' in line for line in frame_lines(app))
    assert not pump.cancel_current()
    await pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_cancel_key_during_model_call_ends_turn_idle():
    app, _ = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())
    backend = _BlockingBackend()
    session = _TurnLoopSession(backend=backend, tools=[], subscriber=renderer.on_agent_event)
    pump = _wire(app, session)

    pump.submit('go')
    await backend.started.wait()
    assert any(' streaming ' in line for line in frame_lines(app))

    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    await session.finished.wait()

    assert not app.is_busy
    assert any(' idle ' in line for line in frame_lines(app))
    assert not pump.cancel_current()
    await pump.aclose()


##
# Quitting


class _QuitDriver(Driver):
    """Snapshots `probe(self)` at the moment `stop` is called, to assert what had already happened by then."""

    def __init__(self, probe) -> None:
        super().__init__()

        self._probe = probe
        self.at_stop: ta.Any = None

    def stop(self) -> None:
        self.at_stop = self._probe(self)
        super().stop()


def test_request_quit_without_hook_stops_driver():
    app, driver = make_app()

    app.request_quit()

    assert driver.stopped


def test_quit_keys_route_through_hook():
    app, driver = make_app()
    quits = []
    app.on_quit = lambda: quits.append('quit')

    app.handle_event(mt.KeyEvent(app_key(AppKey.EXIT)))
    app.handle_event(mt.KeyEvent(mt.Key('escape')))
    app.handle_event(mt.KeyEvent(mt.Key(':'), text=':'))
    app.handle_event(mt.KeyEvent(mt.Key('q'), text='q'))
    app.handle_event(mt.KeyEvent(mt.Key('enter')))

    assert quits == ['quit', 'quit']
    assert not driver.stopped


@pytest.mark.asyncs('asyncio')
async def test_quit_signal_routes_through_hook():
    app, driver = make_app()
    quits = []
    app.on_quit = lambda: quits.append('quit')

    await AppQuitSignal(app=app).quit()

    assert quits == ['quit']
    assert not driver.stopped


@pytest.mark.asyncs('asyncio')
async def test_quit_drains_pump_before_stopping_driver():
    session = BlockingSession()
    driver = _QuitDriver(lambda d: session.first_stopped.is_set())
    app = MinituiChatApp(ta.cast(mt.AsyncioDriver, driver))
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)
    shutdown = Shutdown(pump=pump, driver=ta.cast(mt.AsyncioDriver, driver))
    app.on_quit = shutdown.request

    pump.submit('first')
    await session.first_started.wait()
    pump.submit('second')

    app.handle_event(mt.KeyEvent(app_key(AppKey.EXIT)))
    app.handle_event(mt.KeyEvent(app_key(AppKey.EXIT)))  # a repeat is a no-op, not a second shutdown
    await settle(lambda: driver.stopped)

    assert driver.stopped
    assert driver.at_stop is True
    assert session.prompts == ['first']


@pytest.mark.asyncs('asyncio')
async def test_quit_commits_cancelled_cards_before_driver_stops():
    driver = _QuitDriver(commit_texts)
    app = MinituiChatApp(ta.cast(mt.AsyncioDriver, driver))
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())
    tool = _BlockingTool()
    session = _TurnLoopSession(
        backend=_tool_call_backend('t1', 'block'),
        tools=[tool.tool()],
        subscriber=renderer.on_agent_event,
    )
    pump = _wire(app, session)
    shutdown = Shutdown(pump=pump, driver=ta.cast(mt.AsyncioDriver, driver))
    app.on_quit = shutdown.request

    pump.submit('go')
    await tool.started.wait()
    driver.commits.clear()

    await AppQuitSignal(app=app).quit()
    await settle(lambda: driver.stopped)

    assert driver.stopped
    assert any('block  cancelled' in c for c in driver.at_stop)
    assert driver.at_stop[-1] == '× cancelled\n'
    assert not app.is_busy
