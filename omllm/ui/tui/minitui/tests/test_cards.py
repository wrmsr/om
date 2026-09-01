import typing as ta

import pytest

from omdev.tui import minitui as mt

from ..... import agent as agn
from ..... import harness as har
from ..... import llm
from ..app import AppKey
from ..main import PromptPump
from ..toolcards import tool_card_key
from .utils import BlockingSession
from .utils import app_key
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app


##


def test_tool_cards_update_independently_and_commit_in_start_order():
    app, driver = make_app()

    app.tool_started('call-a', 'alpha', [[mt.Segment('args: a')]])
    app.tool_started('call-b', 'beta', [[mt.Segment('args: b')]])
    running_lines = [line for line in frame_lines(app) if 'running...' in line]
    assert len(running_lines) == 2
    assert 'alpha  running...' in running_lines[0]
    assert 'beta  running...' in running_lines[1]

    app.tool_finished('call-b', 'beta', ok=True)
    lines = frame_lines(app)
    assert any('alpha  running...' in line for line in lines)
    assert any('beta  done' in line for line in lines)

    driver.fire_after(.8)
    assert driver.commits == []

    app.tool_finished('call-a', 'alpha', ok=True)
    driver.fire_after(.8)

    committed = commit_texts(driver)
    assert len(committed) == 2
    assert 'alpha  done' in committed[0]
    assert 'beta  done' in committed[1]


def test_permission_cards_queue_without_orphaning_responses():
    app, _ = make_app()
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

    lines = frame_lines(app)
    assert sum('allow (f10)' in line for line in lines) == 1
    assert any('alpha  awaiting confirmation' in line for line in lines)
    assert any('beta  queued for confirmation' in line for line in lines)

    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_ALLOW)))
    assert responses == [('call-a', True)]
    lines = frame_lines(app)
    assert any('alpha  running...' in line for line in lines)
    assert any('beta  awaiting confirmation' in line for line in lines)
    assert sum('allow (f10)' in line for line in lines) == 1

    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    assert responses == [('call-a', True), ('call-b', False)]
    assert any('beta  denied' in line for line in frame_lines(app))


@pytest.mark.parametrize(('cancelled', 'status'), [(True, 'cancelled'), (False, 'failed')])
def test_aborted_turn_cancels_permissions_and_finalizes_cards(cancelled, status):
    app, driver = make_app()
    responses = []
    cancellations = []

    app.begin_ai_turn()
    driver.commits.clear()
    for key, title in [('call-a', 'alpha'), ('call-b', 'beta')]:
        app.tool_started(key, title, ())

        def on_respond(allowed, *, key=key):
            responses.append((key, allowed))

        def on_cancel(*, key=key):
            cancellations.append(key)

        app.begin_permission_card(key, title, (), on_respond, on_cancel=on_cancel)

    app.abort_ai_turn(cancelled=cancelled)

    assert cancellations == ['call-a', 'call-b']
    assert responses == []
    assert not app.is_busy
    committed = commit_texts(driver)
    assert len(committed) == 3
    assert f'alpha  {status}' in committed[0]
    assert f'beta  {status}' in committed[1]
    assert committed[2].endswith(f' {status}\n')
    assert not any(title in line for title in ('alpha', 'beta') for line in frame_lines(app))


@pytest.mark.asyncs('asyncio')
async def test_key_cancels_current_prompt_and_runs_next():
    app, _ = make_app()
    session = BlockingSession()
    pump = PromptPump(session=ta.cast(har.Session, session), app=app)
    app.on_cancel = pump.cancel_current

    pump.submit('first')
    await session.first_started.wait()
    pump.submit('second')

    app.begin_ai_turn()
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))

    await session.first_stopped.wait()
    await session.second_done.wait()
    assert session.prompts == ['first', 'second']
    assert not pump.cancel_current()

    app.end_ai_turn()
    await pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_prompt_pump_shutdown_drops_queued_prompts():
    app, _ = make_app()
    session = BlockingSession()
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
