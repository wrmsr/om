from omcore import lang

from ..interpreters import ResultStatus
from ..lines import LineRepl
from ..outputs import ListOutputSink
from ..python.interpreter import PythonInterpreter
from ..sessions import Session


##


def make_repl():
    sink = ListOutputSink()
    session = Session({'py': PythonInterpreter(config=PythonInterpreter.Config(allow_await=False))})
    return LineRepl(session, sink), sink


def feed(repl, line):
    return lang.sync_await(repl.feed_line(line))


def test_single_lines_run_at_once():
    repl, sink = make_repl()
    assert repl.prompt == '>>> '
    result = feed(repl, '1 + 1')
    assert result is not None and result.ok
    assert sink.text() == '2\n'
    assert not repl.pending


def test_blocks_accumulate_until_the_closing_blank_line():
    repl, sink = make_repl()
    assert feed(repl, 'def f(x):') is None
    assert repl.pending
    assert repl.prompt == '... '
    assert feed(repl, '    return x + 1') is None
    result = feed(repl, '')
    assert result is not None and result.ok
    assert not repl.pending
    assert feed(repl, 'f(1)').value.must() == 2
    assert sink.text() == '2\n'


def test_blank_lines_outside_a_block_do_nothing():
    repl, sink = make_repl()
    assert feed(repl, '') is None
    assert feed(repl, '   ') is None
    assert sink.text() == ''


def test_invalid_runs_and_reports():
    repl, sink = make_repl()
    result = feed(repl, '1 +')
    assert result is not None and result.status is ResultStatus.ERROR
    assert 'SyntaxError' in sink.text()
    assert not repl.pending


def test_reset_drops_the_buffer():
    repl, sink = make_repl()
    feed(repl, 'def f():')
    repl.reset()
    assert not repl.pending
    assert repl.prompt == '>>> '


def test_exit():
    repl, _ = make_repl()
    assert feed(repl, 'exit()').status is ResultStatus.EXIT
