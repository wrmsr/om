import asyncio
import io

import pytest

from omcore import lang

from ...interpreters import ResultStatus
from ...outputs import ErrorOutput
from ...outputs import ListOutputSink
from ...outputs import NopOutputSink
from ...outputs import ResultOutput
from ...outputs import StdoutOutput
from ..interpreter import PythonInterpreter


##


def run(py, source):
    sink = ListOutputSink()
    result = lang.sync_await(py.execute(source, sink))
    return result, sink


def test_expression_value_is_shown_and_bound():
    py = PythonInterpreter()
    result, sink = run(py, '1 + 1')
    assert result.ok
    assert result.value.must() == 2
    assert sink.outputs == (ResultOutput('2'),)
    assert py.namespace['_'] == 2


def test_statements_are_silent_and_persist():
    py = PythonInterpreter()
    result, sink = run(py, 'x = 5')
    assert result.ok
    assert not result.value.present
    assert sink.outputs == ()
    assert run(py, 'x * 2')[1].text() == '10\n'


def test_none_results_are_not_shown():
    py = PythonInterpreter()
    result, sink = run(py, 'None')
    assert result.ok and result.value.must() is None
    assert sink.outputs == ()


def test_print_is_captured():
    py = PythonInterpreter()
    _, sink = run(py, 'print("hi", 1, sep="-"); print("x", end="")\n"done"')
    assert sink.outputs == (StdoutOutput('hi-1\n'), StdoutOutput('x'), ResultOutput("'done'"))


def test_print_to_a_file_passes_through():
    py = PythonInterpreter({'buf': io.StringIO()})
    _, sink = run(py, 'print("x", file=buf)')
    assert sink.outputs == ()
    assert py.namespace['buf'].getvalue() == 'x\n'


def test_multiple_statements_run_in_order_until_one_fails():
    py = PythonInterpreter()
    result, sink = run(py, 'a = 1\nb = a + 1\nprint(b)\nc = b / 0\nprint("unreached")')
    assert result.status is ResultStatus.ERROR
    assert isinstance(result.error, ZeroDivisionError)
    assert sink.outputs[0] == StdoutOutput('2\n')
    assert isinstance(sink.outputs[1], ErrorOutput)
    assert len(sink.outputs) == 2
    assert py.namespace['b'] == 2
    assert 'c' not in py.namespace


def test_syntax_error():
    py = PythonInterpreter()
    result, sink = run(py, 'nope(')
    assert result.status is ResultStatus.ERROR
    assert isinstance(result.error, SyntaxError)
    (err,) = sink.outputs
    assert isinstance(err, ErrorOutput)
    assert 'SyntaxError' in err.text
    assert '<input>' in err.text


def test_tracebacks_are_trimmed_to_the_users_frames():
    py = PythonInterpreter()
    assert run(py, 'def f():\n    return 1 / 0\n')[0].ok
    result, sink = run(py, 'f()')
    assert result.status is ResultStatus.ERROR
    text = sink.text()
    assert text.startswith('Traceback (most recent call last):')
    assert 'File "<input>", line 1, in <module>' in text
    assert 'File "<input>", line 2, in f' in text
    assert 'interpreter.py' not in text
    assert text.rstrip().endswith('ZeroDivisionError: division by zero')


def test_exit_and_quit():
    py = PythonInterpreter()
    for source in ('exit()', 'quit()', 'exit(3)', 'raise SystemExit'):
        result, sink = run(py, source)
        assert result.status is ResultStatus.EXIT
        assert isinstance(result.error, SystemExit)
        assert sink.outputs == ()
    assert 'Use exit()' in run(py, 'exit')[1].text()


def test_empty_source():
    result, sink = run(PythonInterpreter(), '  \n# only a comment\n')
    assert result.ok and sink.outputs == ()


def test_namespace_is_seeded_and_live():
    py = PythonInterpreter({'answer': 42}, config=PythonInterpreter.Config(module_name='__manhole__'))
    assert run(py, 'answer')[1].text() == '42\n'
    assert run(py, '__name__')[1].text() == "'__manhole__'\n"
    py.namespace['more'] = 1
    assert run(py, 'more + answer')[1].text() == '43\n'


def test_result_binding_can_be_off():
    py = PythonInterpreter(config=PythonInterpreter.Config(bind_result=False))
    run(py, '7')
    assert '_' not in py.namespace


def test_default_sink_catches_output_outside_an_execution():
    default = ListOutputSink()
    py = PythonInterpreter(default_sink=default)
    assert run(py, 'def g():\n    print("later")\n')[0].ok
    py.namespace['g']()  # called back from elsewhere in the process, no execution under way
    assert default.text() == 'later\n'
    assert py.default_sink is default
    py.set_default_sink(None)
    assert py.default_sink is None


def test_a_failing_repr_is_the_codes_error():
    py = PythonInterpreter()
    run(py, 'class B:\n    def __repr__(self):\n        raise ValueError("no repr")\n')
    result, sink = run(py, 'B()')
    assert result.status is ResultStatus.ERROR
    assert isinstance(result.error, ValueError)
    assert 'no repr' in sink.text()


def test_builtins_are_private():
    py = PythonInterpreter()
    assert run(py, 'print is __builtins__["print"]')[1].text() == 'True\n'
    assert run(py, 'import builtins\nbuiltins.print is print')[1].text() == 'False\n'


def test_await_can_be_disallowed():
    py = PythonInterpreter(config=PythonInterpreter.Config(allow_await=False))
    result, sink = run(py, 'await something')
    assert result.status is ResultStatus.ERROR
    assert 'SyntaxError' in sink.text()


def test_a_real_await_cannot_run_without_a_loop():
    py = PythonInterpreter({'asyncio': asyncio})
    with pytest.raises(lang.SyncAwaitCoroutineNotTerminatedError):
        run(py, 'await asyncio.sleep(0)')


def test_completion():
    py = PythonInterpreter({'alpha': 1})
    assert [c.text for c in py.complete('alp', 3)] == ['alpha']


@pytest.mark.asyncs('asyncio')
async def test_top_level_await():
    py = PythonInterpreter({'asyncio': asyncio})
    sink = ListOutputSink()
    result = await py.execute('await asyncio.sleep(0)\nx = await asyncio.sleep(0, result=41)\nx + 1', sink)
    assert result.ok
    assert result.value.must() == 42
    assert sink.outputs == (ResultOutput('42'),)
    assert py.namespace['x'] == 41


@pytest.mark.asyncs('asyncio')
async def test_await_errors_are_reported_like_any_other():
    py = PythonInterpreter({'asyncio': asyncio})
    sink = ListOutputSink()
    result = await py.execute('async def boom():\n    raise KeyError("k")\nawait boom()', sink)
    assert result.status is ResultStatus.ERROR
    assert isinstance(result.error, KeyError)
    assert 'in boom' in sink.text()


@pytest.mark.asyncs('asyncio')
async def test_concurrent_executions_keep_their_output_apart():
    py = PythonInterpreter({'asyncio': asyncio, 'gate': asyncio.Event()})
    a = ListOutputSink()
    b = ListOutputSink()

    async def first():
        await py.execute('print("a1")\nawait gate.wait()\nprint("a2")', a)

    async def second():
        await py.execute('print("b1")\ngate.set()\nprint("b2")', b)

    await asyncio.gather(first(), second())
    assert a.text() == 'a1\na2\n'
    assert b.text() == 'b1\nb2\n'


@pytest.mark.asyncs('asyncio')
async def test_cancellation_propagates():
    py = PythonInterpreter({'asyncio': asyncio})
    task = asyncio.ensure_future(py.execute('await asyncio.sleep(60)', NopOutputSink()))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
