"""
Diffs end to end on the bare frontend, through its own injector wiring: a real agent running the real edit tool over a
scripted model, asking at a (scripted) prompt. Everything bare shows is scrollback, so the diff appears above the prompt
asking about it - and only there, the result not repeating it.
"""
import collections
import io
import os.path

import pytest

from omcore import inject as inj

from ..... import llm
from .....agent.tests.scripted import text_message
from .....agent.tests.scripted import tool_call_message
from ...config import Config
from ...rendering import TerminalTextDisplayer
from ...rendering import TerminalTextRenderer
from ...tests.headless import bind_scripted_backend
from ...tests.headless import headless_tui
from ..inject import bind_bare
from ..input import InputManager


##


class _ScriptedInputManager(InputManager):
    """Answers prompts from a script, noting each prompt and everything displayed by the time it was given."""

    def __init__(self, out, answers):
        super().__init__()

        self._out = out
        self._answers = collections.deque(answers)

        self.prompts = []

    async def input(self, prompt=None):
        self.prompts.append((prompt, self._out.getvalue()))
        return self._answers.popleft()


class _Run:
    def __init__(self, tmp_path, *, answers=()):
        super().__init__()

        self.root = os.path.realpath(tmp_path)
        self.path = os.path.join(self.root, 'f.py')
        with open(self.path, 'w') as f:
            f.write('one\ntwo\nthree\n')

        self.out = io.StringIO()
        self.input_manager = _ScriptedInputManager(self.out, answers)

        # The rendered diff's own header line for this one-line change.
        self.diff_header = f'{self.path} (1 additions, 1 removals)'

    def read(self):
        with open(self.path) as f:
            return f.read()

    def tui(self):
        return headless_tui(inj.override(
            bind_bare(Config(
                model='scripted',
                immediate=True,
                in_memory=True,
                cwd=self.root,
                fs=True,
                allow_fs_reads=True,
            )),

            inj.bind(InputManager, to_const=self.input_manager),
            inj.bind(TerminalTextDisplayer, to_const=TerminalTextDisplayer(
                file=self.out,
                renderer=TerminalTextRenderer(width=100, color_depth=None),
            )),

            bind_scripted_backend(
                tool_call_message(llm.ToolCall(
                    id='edit-1',
                    name='edit',
                    args={'file_path': self.path, 'old_string': 'two\n', 'new_string': 'TWO\n'},
                )),
                text_message('edited'),
            ),
        ))


@pytest.mark.asyncs('asyncio')
async def test_bare_asks_beneath_the_diff_and_does_not_repeat_it(tmp_path):
    run = _Run(tmp_path, answers=['y'])

    async with run.tui() as tui:
        await tui.agent.prompt('edit it')

    [(prompt, shown)] = run.input_manager.prompts
    assert prompt == f"edit :: FsPermissionTarget(path='{run.path}', mode='w') (y/n) "
    assert run.diff_header in shown
    assert 'two' in shown and 'TWO' in shown

    assert run.read() == 'one\nTWO\nthree\n'

    output = run.out.getvalue()
    assert output.count(run.diff_header) == 1
    assert output.rstrip().endswith('edited')


@pytest.mark.asyncs('asyncio')
async def test_bare_shows_a_refused_diff_once_and_writes_nothing(tmp_path):
    run = _Run(tmp_path, answers=['n'])

    async with run.tui() as tui:
        await tui.agent.prompt('edit it')

    assert len(run.input_manager.prompts) == 1
    assert run.read() == 'one\ntwo\nthree\n'
    assert run.out.getvalue().count(run.diff_header) == 1


@pytest.mark.asyncs('asyncio')
async def test_bare_shows_an_unasked_edits_diff_as_its_result(tmp_path):
    run = _Run(tmp_path)

    async with run.tui() as tui:
        # As `--yolo` does: the configured rules ask first and would win, so they go.
        await tui.commands.parse('permissions clear').run()
        rule = f'{{"glob":"{run.root}/**","modes":["r","w"]}}'
        await tui.commands.parse(f"permissions add allow glob_fs '{rule}'").run()
        await tui.agent.prompt('edit it')

    assert run.input_manager.prompts == []
    assert run.read() == 'one\nTWO\nthree\n'
    assert run.out.getvalue().count(run.diff_header) == 1
