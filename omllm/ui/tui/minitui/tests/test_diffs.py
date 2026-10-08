"""
Diffs end to end on the minitui surface: a real agent running the real edit tool over a scripted model, asking under a
real decider through the card asker. The change is shown on the confirmation card before anything is written, and the
same diff is what the finished card commits to scrollback.
"""
import os.path

import pytest

from omdev import minitui as mt

from ..... import agent as agn
from ..... import llm
from .....agent.tests.scripted import scripted_backend
from .....agent.tests.scripted import text_message
from .....agent.tests.scripted import tool_call_message
from .....core import ui
from ...config import Config
from ..app import AppKey
from ..input import CardPermissionAsker
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from ..promptpump import PromptPump
from ..toolcards import card_text_rows
from ..toolcards import tool_call_summary
from .utils import app_key
from .utils import commit_texts
from .utils import make_agent
from .utils import make_app
from .utils import settle
from .utils import settle_idle


##


# The rendered diff's own header line for a one-line change, distinctive enough to find it by.
_DIFF_HEADER = '(1 additions, 1 removals)'


class _Run:
    def __init__(self, tmp_path, *, write_state):
        super().__init__()

        self.root = os.path.realpath(tmp_path)
        self.path = os.path.join(self.root, 'f.py')
        with open(self.path, 'w') as f:
            f.write('one\ntwo\nthree\n')

        # Wide enough for the card's header to keep a temp path and its status on one row.
        self.app, self.driver = make_app()
        self.driver.surface.width = 120

        workspace = os.path.join(self.root, '**')
        self.decider = agn.StandardPermissionDecider(
            manager=agn.StandardPermissionsManager([
                agn.PermissionRule(agn.GlobFsPermissionMatcher(workspace, ['r']), agn.PermissionState.ALLOW),
                agn.PermissionRule(agn.GlobFsPermissionMatcher(workspace, ['w']), write_state),
            ]),
            asker=CardPermissionAsker(app=self.app),
        )

        self.backend = scripted_backend(
            tool_call_message(llm.ToolCall(
                id='edit-1',
                name='edit',
                args={'file_path': self.path, 'old_string': 'two\n', 'new_string': 'TWO\n'},
            )),
            text_message('edited'),
        )

    def read(self):
        with open(self.path) as f:
            return f.read()

    async def start(self):
        edit = agn.EditTool(permissions=self.decider, fs=agn.LocalFsOps())
        self.agent = agent = await make_agent(self.backend, tools=[edit.tool()])
        await agent.update_state(lambda s: agn.State(
            context=s.context,
            tool_env=agn.ToolEnvironment(cwd=self.root),
        ))

        renderer = AgentEventRenderer(app=self.app, text_displayer=MinituiTextDisplayer(app=self.app), config=Config())
        agent.subscribe(renderer.on_agent_event)

        self.pump = PromptPump(agent=agent, app=self.app)
        self.pump.submit('edit it')

    def frame(self):
        return [line.text for line in self.app.render(self.app.width, 60).lines]

    def shows(self, text):
        return any(text in line for line in self.frame())

    async def finish(self):
        # The run is over once the model has answered the tool result: prompt, tool call, tool result, answer.
        await settle_idle(self.agent, lambda: len(self.agent.state.context.messages or ()) == 4)
        self.driver.fire_after(.8)

    def committed_card(self):
        [card] = [c for c in commit_texts(self.driver) if 'edit  ' in c]
        return card


@pytest.mark.asyncs('asyncio')
async def test_edit_is_confirmed_over_its_diff_and_commits_it(tmp_path):
    run = _Run(tmp_path, write_state=agn.PermissionState.ASK)
    await run.start()

    await settle(lambda: run.shows('awaiting confirmation'), max_steps=200)
    lines = run.frame()

    # Nothing is written while the user looks at what would be.
    assert run.read() == 'one\ntwo\nthree\n'

    # The card opened itself onto the diff, and the choice comes after it.
    header = next(i for i, line in enumerate(lines) if 'edit  ' in line and 'awaiting confirmation' in line)
    assert lines[header].startswith('[-] ? edit')
    diff = next(i for i, line in enumerate(lines) if _DIFF_HEADER in line)
    choice = next(i for i, line in enumerate(lines) if 'allow (f10)' in line)
    assert header < diff < choice
    assert any('two' in line and 'TWO' in line for line in lines[diff:choice])

    run.app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_ALLOW)))
    await run.finish()

    assert run.read() == 'one\nTWO\nthree\n'

    # Scrollback keeps the card opened onto the same diff - now as what was done.
    card = run.committed_card()
    assert 'edit  ' in card and '  done' in card
    assert card.startswith('[-] ✓ edit')
    assert _DIFF_HEADER in card
    assert 'allow (f10)' not in card

    await run.pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_denied_edit_commits_the_refused_diff_as_denied(tmp_path):
    run = _Run(tmp_path, write_state=agn.PermissionState.ASK)
    await run.start()

    await settle(lambda: run.shows('awaiting confirmation'), max_steps=200)
    run.app.handle_event(mt.KeyEvent(app_key(AppKey.CARD_DENY)))
    await run.finish()

    assert run.read() == 'one\ntwo\nthree\n'

    card = run.committed_card()
    assert card.startswith('[-] ✗ edit')
    assert '  denied' in card
    assert 'failed' not in card
    assert _DIFF_HEADER in card

    await run.pump.aclose()


@pytest.mark.asyncs('asyncio')
async def test_edit_allowed_outright_still_commits_its_diff(tmp_path):
    run = _Run(tmp_path, write_state=agn.PermissionState.ALLOW)
    await run.start()
    await run.finish()

    assert run.read() == 'one\nTWO\nthree\n'

    # Never asked, so never opened by a confirmation - the result's display opens it.
    card = run.committed_card()
    assert card.startswith('[-] ✓ edit')
    assert _DIFF_HEADER in card

    await run.pump.aclose()


##


def test_card_text_rows_fit_beside_the_detail_indent():
    width = 60
    rows = card_text_rows(['changing:\n', ui.DiffText(old='a\nb\n', new='a\nB\n', path='f.py')], width)

    assert mt.segments_text(rows[0]) == 'changing:'
    assert any(_DIFF_HEADER in mt.segments_text(row) for row in rows)
    assert all(len(mt.segments_text(row)) <= width - mt.CARD_DETAIL_INDENT for row in rows)

    # A card at that width lays them out as given, never re-wrapping the diff's fixed-width rows.
    card = mt.Card(detail=rows, expanded=True)
    assert len(card.render(width)) == 1 + len(rows)

    # A trailing newline ends the text's last row rather than starting another.
    assert [mt.segments_text(row) for row in card_text_rows('x\n', width)] == ['x']


def test_tool_call_summary_flattens_ui_text():
    async def execute(ctx):
        raise AssertionError

    tool = agn.Tool(
        llm_tool=llm.Tool(name='styled'),
        executor=execute,
        summarizer=lambda ctx: ui.Text.of('edit ', ui.Text.of('f.py').style(bold=True), '\n'),
    )

    assert tool_call_summary(agn.ToolContext(tool=tool, args={})) == 'edit f.py'
