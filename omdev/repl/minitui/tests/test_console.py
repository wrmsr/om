import asyncio

import pytest

from ....minitui.controls.textarea import TextArea
from ....minitui.text.segments import segments_text
from ...asyncio import AsyncioRunner
from ...python.interpreter import PythonInterpreter
from ...runners import ImmediateRunner
from ...sessions import Session
from ..console import Console


##


def make_console(runner=None, namespace=None, **kwargs):
    commits: list = []
    textarea = TextArea()
    session = Session({
        'py': PythonInterpreter(namespace, config=PythonInterpreter.Config(allow_await=runner is not None)),
        'py2': PythonInterpreter(config=PythonInterpreter.Config(module_name='__second__')),
    })
    console = Console(
        session,
        textarea,
        runner=runner if runner is not None else ImmediateRunner(),
        commit=commits.append,
        width=lambda: 40,
        **kwargs,
    )
    return console, textarea, commits


def committed(commits):
    return [[segments_text(row) for row in rows] for rows in commits]


def test_activation_takes_and_returns_the_textarea():
    console, textarea, _ = make_console()
    assert (textarea.prompt, textarea.highlighter) == ('', None)

    console.activate()
    assert console.is_active
    assert textarea.prompt == '>>> '
    highlighter = textarea.highlighter
    assert highlighter is not None

    console.deactivate()
    assert (textarea.prompt, textarea.highlighter) == ('', None)


def test_input_is_highlighted_under_the_repl_tags():
    console, textarea, _ = make_console()
    console.activate()
    textarea.set_text('def foo(x):')
    (row,) = textarea.render(40)
    assert [(seg.text, seg.style) for seg in row][:2] == [('>>> ', 'repl.prompt'), ('def', 'repl.code.keyword')]


def test_submit_commits_echo_outputs_and_a_separator():
    console, _, commits = make_console()
    console.activate()
    console.submit('print("a")\n[1, 2]')
    assert committed(commits) == [
        ['>>> print("a")', '... [1, 2]'],
        ['a'],
        ['[1, 2]'],
        [''],
    ]
    assert commits[1][0][0].style == 'repl.stdout'
    assert commits[2][0][0].style == 'repl.result'
    assert not console.is_running


def test_blank_submissions_are_ignored():
    console, _, commits = make_console()
    console.submit('   \n')
    assert commits == []


def test_errors_are_committed():
    console, _, commits = make_console()
    console.submit('1 / 0')
    rows = committed(commits)[1]
    assert rows[0] == 'Traceback (most recent call last):'
    assert rows[-1] == 'ZeroDivisionError: division by zero'
    assert commits[1][0][0].style == 'repl.error'


def test_switching_follows_the_session():
    changes = []
    console, textarea, _ = make_console(on_change=lambda: changes.append(True))
    console.activate()
    console.switch('py2')
    assert console.session.active_name == 'py2'
    assert console.language.name == 'python'
    assert textarea.prompt == '>>> '
    console.submit('__name__')
    assert changes


def test_exit_fires_on_exit():
    exits = []
    console, _, commits = make_console(on_exit=lambda: exits.append(True))
    console.submit('exit()')
    assert exits == [True]
    assert committed(commits) == [['>>> exit()'], ['']]


def test_status_parts():
    console, _, _ = make_console()
    parts = console.status_parts()
    assert parts[0] == ('python', 'repl.language')
    assert parts[1] == ('', 'status.dim')


@pytest.mark.asyncs('asyncio')
async def test_executions_queue_and_cancel():
    runner = AsyncioRunner()
    gate = asyncio.Event()
    console, _, commits = make_console(runner, namespace={'asyncio': asyncio, 'gate': gate})
    try:
        console.submit('await gate.wait()\n"first"')
        console.submit('"second"')
        await asyncio.sleep(0)
        assert console.is_running
        assert console.queued == 1
        assert console.status_parts()[1:] == [('  running', 'status.dim'), ('  +1 queued', 'status.dim')]

        gate.set()
        for _ in range(10):
            await asyncio.sleep(0)
        assert not console.is_running
        assert committed(commits) == [
            ['>>> await gate.wait()', '... "first"'],
            ['>>> "second"'],
            ["'first'"],
            [''],
            ["'second'"],
            [''],
        ]

        console.submit('await asyncio.sleep(60)')
        await asyncio.sleep(0)
        assert console.cancel()
        for _ in range(10):
            await asyncio.sleep(0)
        assert not console.is_running
        assert committed(commits)[-2:] == [['interrupted'], ['']]
        assert not console.cancel()
    finally:
        await runner.aclose()
