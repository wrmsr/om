from omcore import check
from omcore.term import styled as tst

from ....minitui.text.segments import segments_text
from ....minitui.text.styles import Style
from ...languages import PYTHON_LANGUAGE
from ...outputs import ErrorOutput
from ...outputs import NoteOutput
from ...outputs import ResultOutput
from ...outputs import StdoutOutput
from ...outputs import TerminalOutput
from ..rendering import render_echo
from ..rendering import render_note
from ..rendering import render_output


##


def texts(rows):
    return [segments_text(row) for row in rows]


def tags(rows):
    return [[seg.style for seg in row] for row in rows]


def concrete(seg):
    return check.isinstance(seg.style, Style)


def test_echo():
    rows = render_echo(PYTHON_LANGUAGE, 'def f():\n    return 1\n', 40)
    assert texts(rows) == ['>>> def f():', '...     return 1', '...']  # trailing blanks are dropped by the wrap
    assert tags(rows)[0] == ['repl.prompt', 'repl.echo']
    assert tags(rows)[2] == ['repl.prompt']


def test_echo_wraps_to_width():
    rows = render_echo(PYTHON_LANGUAGE, 'x' * 50, 20)
    assert all(len(t) <= 20 for t in texts(rows))
    assert ''.join(texts(rows)).replace('>>> ', '') == 'x' * 50


def test_output_rows():
    assert texts(render_output(StdoutOutput('a\nb\n'), 40)) == ['a', 'b']
    assert texts(render_output(StdoutOutput('partial'), 40)) == ['partial']
    assert texts(render_output(StdoutOutput('\n'), 40)) == ['']
    assert tags(render_output(ResultOutput('1'), 40)) == [['repl.result']]
    rows = render_output(ErrorOutput('Traceback:\n  boom'), 40)
    assert texts(rows) == ['Traceback:', '  boom']
    assert all(t == ['repl.error'] for t in tags(rows))


def test_output_is_cleaned_and_wrapped():
    rows = render_output(StdoutOutput('a\tb\r\n\x1b[31mred'), 40)
    assert texts(rows) == ['a   b', '^[[31mred']
    rows = render_output(StdoutOutput('y' * 30), 10)
    assert all(len(t) <= 10 for t in texts(rows))


def test_terminal_output_rows():
    rows = render_output(TerminalOutput('plain \x1b[0;1;31mred\x1b[0m\n\nlast\n'), 40)
    assert texts(rows) == ['plain red', '', 'last']
    plain, red = rows[0]
    assert (plain.text, plain.style) == ('plain ', 'repl.stdout')
    assert red.text == 'red'
    assert (concrete(red).bold, concrete(red).fg) == (True, tst.RED)
    assert tags(rows)[2] == ['repl.stdout']

    assert texts(render_output(TerminalOutput('still being written: '), 40)) == ['still being written:']


def test_terminal_output_is_cleaned_and_wrapped():
    rows = render_output(TerminalOutput('\x1b[0;31m' + 'r' * 30 + '\x1b[0m\x1b]0;stray\n'), 10)
    assert all(len(t) <= 10 for t in texts(rows))
    assert ''.join(texts(rows)) == 'r' * 30 + '^[]0;stray'
    assert all(seg.style == 'repl.stdout' or concrete(seg).fg == tst.RED for row in rows for seg in row)


def test_note_output():
    rows = render_output(NoteOutput('[exit 1]'), 40)
    assert texts(rows) == ['[exit 1]']
    assert tags(rows) == [['repl.note']]


def test_note():
    assert tags(render_note('hm', 40)) == [['repl.note']]
