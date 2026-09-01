import asyncio
import typing as ta

import pytest

from omdev.tui import minitui as mt

from ..... import agent as agn
from ..... import harness as har
from ..... import llm
from ..app import MinituiChatApp
from ..main import PromptPump
from ..toolcards import tool_card_key


##


class _Clock:
    def __init__(self) -> None:
        super().__init__()

        self.now = 0.

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class _Surface:
    def __init__(self, width: int = 80) -> None:
        super().__init__()

        self.width = width


class _Driver:
    def __init__(self) -> None:
        super().__init__()

        self.clock = _Clock()
        self.surface = _Surface()
        self.timers = mt.Timers(self.clock)
        self.commits: list[tuple[mt.Line, ...]] = []
        self.invalidations = 0
        self.stopped = False

    def commit(self, lines) -> None:
        self.commits.append(tuple(lines))

    def invalidate(self) -> None:
        self.invalidations += 1

    def stop(self) -> None:
        self.stopped = True


class _BlockingSession:
    def __init__(self) -> None:
        super().__init__()

        self.prompts: list[str] = []
        self.first_started = asyncio.Event()
        self.first_stopped = asyncio.Event()
        self.second_done = asyncio.Event()
        self._never = asyncio.Event()

    async def prompt(self, text: str) -> None:
        self.prompts.append(text)
        if len(self.prompts) == 1:
            self.first_started.set()
            try:
                await self._never.wait()
            finally:
                self.first_stopped.set()
        else:
            self.second_done.set()


def _make_app():
    driver = _Driver()
    return MinituiChatApp(ta.cast(mt.AsyncioDriver, driver)), driver


def _frame_lines(app):
    return [line.text for line in app.render(80, 24).lines]


def _commit_texts(driver):
    return ['\n'.join(line.text for line in commit) for commit in driver.commits]


def test_tool_cards_update_independently_and_commit_in_start_order():
    app, driver = _make_app()

    app.tool_started('call-a', 'alpha', [[mt.Segment('args: a')]])
    app.tool_started('call-b', 'beta', [[mt.Segment('args: b')]])
    running_lines = [line for line in _frame_lines(app) if 'running...' in line]
    assert len(running_lines) == 2
    assert 'alpha  running...' in running_lines[0]
    assert 'beta  running...' in running_lines[1]

    app.tool_finished('call-b', 'beta', ok=True)
    lines = _frame_lines(app)
    assert any('alpha  running...' in line for line in lines)
    assert any('beta  done' in line for line in lines)

    driver.clock.advance(.8)
    driver.timers.fire_due()
    assert driver.commits == []

    app.tool_finished('call-a', 'alpha', ok=True)
    driver.clock.advance(.8)
    driver.timers.fire_due()

    committed = _commit_texts(driver)
    assert len(committed) == 2
    assert 'alpha  done' in committed[0]
    assert 'beta  done' in committed[1]


def test_permission_cards_queue_without_orphaning_responses():
    app, _ = _make_app()
    responses = []

    app.tool_started('call-a', 'alpha', ())
    app.tool_started('call-b', 'beta', ())
    app.begin_permission_card(
        'call-a',
        'alpha',
        [[mt.Segment('target: a')]],
        lambda allowed: responses.append(('call-a', allowed)),
    )
    app.begin_permission_card(
        'call-b',
        'beta',
        [[mt.Segment('target: b')]],
        lambda allowed: responses.append(('call-b', allowed)),
    )

    lines = _frame_lines(app)
    assert sum('allow (f10)' in line for line in lines) == 1
    assert any('alpha  awaiting confirmation' in line for line in lines)
    assert any('beta  queued for confirmation' in line for line in lines)

    app.handle_event(mt.KeyEvent(mt.Key('f10')))
    assert responses == [('call-a', True)]
    lines = _frame_lines(app)
    assert any('alpha  running...' in line for line in lines)
    assert any('beta  awaiting confirmation' in line for line in lines)
    assert sum('allow (f10)' in line for line in lines) == 1

    app.handle_event(mt.KeyEvent(mt.Key('f2')))
    assert responses == [('call-a', True), ('call-b', False)]
    assert any('beta  denied' in line for line in _frame_lines(app))


@pytest.mark.parametrize(('cancelled', 'status'), [(True, 'cancelled'), (False, 'failed')])
def test_aborted_turn_cancels_permissions_and_finalizes_cards(cancelled, status):
    app, driver = _make_app()
    responses = []
    cancellations = []

    app.begin_ai_turn()
    driver.commits.clear()
    for key, title in [('call-a', 'alpha'), ('call-b', 'beta')]:
        app.tool_started(key, title, ())
        app.begin_permission_card(
            key,
            title,
            (),
            lambda allowed, key=key: responses.append((key, allowed)),
            on_cancel=lambda key=key: cancellations.append(key),
        )

    app.abort_ai_turn(cancelled=cancelled)

    assert cancellations == ['call-a', 'call-b']
    assert responses == []
    assert not app.is_busy
    committed = _commit_texts(driver)
    assert len(committed) == 2
    assert f'alpha  {status}' in committed[0]
    assert f'beta  {status}' in committed[1]
    assert not any(title in line for title in ('alpha', 'beta') for line in _frame_lines(app))


@pytest.mark.asyncs('asyncio')
async def test_escape_cancels_current_prompt_and_runs_next():
    app, _ = _make_app()
    session = _BlockingSession()
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)
    app.on_cancel = pump.cancel_current

    pump.submit('first')
    await session.first_started.wait()
    pump.submit('second')

    app.begin_ai_turn()
    app.handle_event(mt.KeyEvent(mt.Key('escape')))
    app.handle_event(mt.KeyEvent(mt.Key('escape')))

    await session.first_stopped.wait()
    await session.second_done.wait()
    assert session.prompts == ['first', 'second']
    assert not pump.cancel_current()

    app.end_ai_turn()
    await pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_prompt_pump_shutdown_drops_queued_prompts():
    app, _ = _make_app()
    session = _BlockingSession()
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)

    pump.submit('first')
    await session.first_started.wait()
    pump.submit('second')
    await pump.aclose()

    assert session.prompts == ['first']
    assert session.first_stopped.is_set()


def test_tool_card_key_uses_llm_call_identity():
    context = agn.ToolContext(
        args={},
        llm_tool_call=llm.ToolCall('call-a', 'alpha', {}),
    )
    assert tool_card_key(context) == 'call-a'

    context_without_call = agn.ToolContext(args={})
    assert tool_card_key(context_without_call) == f'context:{id(context_without_call)}'
