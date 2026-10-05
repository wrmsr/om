import pytest

from omdev import minitui as mt

from ..... import agent as agn
from ..... import llm
from .....agent.tests.scripted import scripted_backend
from .....agent.tests.scripted import text_message
from ...config import Config
from ..app import AppKey
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from ..promptpump import PromptPump
from ..toolcards import tool_call_summary
from ..toolcards import tool_card_key
from .utils import FirstInvocationGate
from .utils import app_key
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_agent
from .utils import make_app
from .utils import settle_idle
from .utils import user_texts


##


def test_tool_cards_update_independently_and_commit_in_start_order():
    app, driver = make_app()

    app.tool_started('call-a', 'alpha', [[mt.Segment('args: a')]], call_summary='file-a')
    app.tool_started('call-b', 'beta', [[mt.Segment('args: b')]], call_summary='file-b')
    running_lines = [line for line in frame_lines(app) if 'running...' in line]
    assert len(running_lines) == 2
    assert 'alpha  file-a  running...' in running_lines[0]
    assert 'beta  file-b  running...' in running_lines[1]

    app.tool_finished('call-b', 'beta', ok=True)
    lines = frame_lines(app)
    assert any('alpha  file-a  running...' in line for line in lines)
    assert any('beta  file-b  done' in line for line in lines)

    driver.fire_after(.8)
    assert driver.commits == []

    app.tool_finished('call-a', 'alpha', ok=True)
    driver.fire_after(.8)

    committed = commit_texts(driver)
    assert len(committed) == 2
    assert 'alpha  file-a  done' in committed[0]
    assert 'beta  file-b  done' in committed[1]


def test_tool_cards_commit_exactly_as_displayed():
    # A live card carries the trailing blank row its committed form gets, so finalizing it moves nothing on screen.
    app, driver = make_app()

    app.tool_started('call-a', 'alpha', ())
    app.tool_started('call-b', 'beta', ())
    lines = frame_lines(app)
    a = next(i for i, line in enumerate(lines) if 'alpha  running...' in line)
    assert lines[a + 1] == ''
    assert 'beta  running...' in lines[a + 2]
    assert lines[a + 3] == ''

    app.tool_finished('call-a', 'alpha', ok=True)
    lines = frame_lines(app)
    a = next(i for i, line in enumerate(lines) if 'alpha  done' in line)
    live_card = lines[a:a + 2]
    assert live_card[1] == ''

    driver.fire_after(.8)
    assert commit_texts(driver) == ['\n'.join(live_card)]
    assert len(frame_lines(app)) == len(lines) - len(live_card)


def test_permission_cards_queue_without_orphaning_responses():
    app, _ = make_app()
    responses = []

    app.tool_started('call-a', 'alpha', (), call_summary='subject-a')
    app.tool_started('call-b', 'beta', (), call_summary='subject-b')
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
    assert any('alpha  subject-a  awaiting confirmation' in line for line in lines)
    assert any('beta  subject-b  queued for confirmation' in line for line in lines)

    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_ALLOW)))
    assert responses == [('call-a', True)]
    lines = frame_lines(app)
    assert any('alpha  subject-a  running...' in line for line in lines)
    assert any('beta  subject-b  awaiting confirmation' in line for line in lines)
    assert sum('allow (f10)' in line for line in lines) == 1

    app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    assert responses == [('call-a', True), ('call-b', False)]
    assert any('beta  subject-b  denied' in line for line in frame_lines(app))


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
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())
    gate = FirstInvocationGate()
    agent = await make_agent(scripted_backend(text_message('one'), text_message('two'), stream=True, gate=gate))
    agent.subscribe(renderer.on_agent_event)
    pump = PromptPump(agent=agent, app=app)
    app.on_cancel = pump.cancel_current

    pump.submit('first')
    await gate.started.wait()
    pump.submit('second')

    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))
    app.handle_event(mt.KeyEvent(app_key(AppKey.CANCEL)))

    await gate.stopped.wait()
    await settle_idle(agent, lambda: len(user_texts(agent)) == 2)

    # The cancelled prompt stays in the transcript as far as it got, and the one queued behind it ran to its answer.
    assert user_texts(agent) == ['first', 'second']
    assert [type(m) for m in agent.state.context.messages or ()] == [
        llm.UserMessage,
        agn.InfoAgentMessage,
        llm.UserMessage,
        llm.AiMessage,
    ]
    assert not app.is_busy
    assert not pump.cancel_current()

    await pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_prompt_pump_shutdown_drops_queued_prompts():
    app, _ = make_app()
    gate = FirstInvocationGate()
    agent = await make_agent(scripted_backend(text_message('one'), text_message('two'), stream=True, gate=gate))
    pump = PromptPump(agent=agent, app=app)

    pump.submit('first')
    await gate.started.wait()
    pump.submit('second')
    await pump.aclose()

    assert user_texts(agent) == ['first']
    assert gate.stopped.is_set()


def test_tool_card_key_uses_llm_call_identity():
    context = agn.ToolContext(
        args={},
        llm_tool_call=llm.ToolCall('call-a', 'alpha', {}),
    )
    assert tool_card_key(context) == 'call-a'

    context_without_call = agn.ToolContext(args={})
    assert tool_card_key(context_without_call) == f'context:{id(context_without_call):x}'


def test_tool_call_summary_supports_bare_tools_and_normalizes_text():
    async def execute(ctx):
        raise AssertionError

    tool = agn.Tool(
        llm_tool=llm.Tool(name='bare'),
        executor=execute,
        summarizer=lambda ctx: f'  {ctx.args["value"]}\n  next  ',
    )
    context = agn.ToolContext(tool=tool, args={'value': 'first'})

    assert tool_call_summary(context) == 'first next'


def test_tool_call_summary_ignores_missing_and_broken_summarizers():
    async def execute(ctx):
        raise AssertionError

    plain_tool = agn.Tool(llm_tool=llm.Tool(name='plain'), executor=execute)
    assert tool_call_summary(agn.ToolContext(tool=plain_tool, args={})) is None

    def raise_summary(ctx):
        raise ValueError

    broken_tool = agn.Tool(
        llm_tool=llm.Tool(name='broken'),
        executor=execute,
        summarizer=raise_summary,
    )
    assert tool_call_summary(agn.ToolContext(tool=broken_tool, args={})) is None
