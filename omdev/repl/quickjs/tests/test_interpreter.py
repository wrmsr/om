import asyncio

import pytest

from omcore import lang

from ...asyncio import AsyncioThreadExecutor
from ...executors import Executor
from ...interpreters import InterpreterBusyError
from ...interpreters import ResultStatus
from ...languages import JAVASCRIPT_LANGUAGE
from ...outputs import ErrorOutput
from ...outputs import ListOutputSink
from ...outputs import ResultOutput
from ...outputs import StdoutOutput
from ..interpreter import QuickjsInterpreter
from ..interpreter import quickjs_available


quickjs = pytest.importorskip('omdev.js.quickjs')


##


def run(js, source):
    sink = ListOutputSink()
    result = lang.sync_await(js.execute(source, sink))
    return result, sink


def test_available():
    assert quickjs_available()


def test_values():
    js = QuickjsInterpreter()
    assert js.language is JAVASCRIPT_LANGUAGE
    cases = {
        '1 + 2': '3',
        '1.5 * 2': '3.0',
        '"a" + "b"': '"ab"',
        'true': 'true',
        '[1, {a: "b"}]': '[1,{"a":"b"}]',
        '(x) => x': '[Function (anonymous)]',
        'function named(a) {}; named': '[Function: named]',
        'new Error("boom")': 'Error: boom',
        'Symbol("s")': 'Symbol(s)',
        '[1,2].map(x => x * 2)': '[2,4]',
    }
    for source, expected in cases.items():
        result, sink = run(js, source)
        assert result.ok, source
        assert sink.outputs == (ResultOutput(expected),), source


def test_undefined_results_are_silent_and_state_persists():
    js = QuickjsInterpreter()
    result, sink = run(js, 'let counter = 10')
    assert result.ok and sink.outputs == ()
    assert run(js, 'undefined')[1].outputs == ()
    assert run(js, 'counter += 5')[1].text() == '15\n'


def test_console_output_is_captured():
    js = QuickjsInterpreter()
    _, sink = run(js, 'console.log("hi", 1, {a: 1}); print("p"); console.error("e"); "done"')
    assert sink.outputs == (
        StdoutOutput('hi 1 {"a":1}\n'),
        StdoutOutput('p\n'),
        StdoutOutput('e\n'),
        ResultOutput('"done"'),
    )


def test_console_can_be_left_out():
    js = QuickjsInterpreter(config=QuickjsInterpreter.Config(install_console=False))
    assert run(js, 'typeof console')[1].text() == '"undefined"\n'


def test_errors():
    js = QuickjsInterpreter()
    result, sink = run(js, 'console.log("before"); nope()')
    assert result.status is ResultStatus.ERROR
    assert isinstance(result.error, quickjs.JsError)
    assert sink.outputs[0] == StdoutOutput('before\n')
    (err,) = sink.outputs[1:]
    assert isinstance(err, ErrorOutput)
    assert err.text.startswith('ReferenceError: nope is not defined')
    assert '<input>' in err.text

    result, sink = run(js, 'this is not js')
    assert result.status is ResultStatus.ERROR
    assert 'SyntaxError' in sink.text()


def test_promises_settle():
    js = QuickjsInterpreter()
    assert run(js, 'Promise.resolve(7)')[1].text() == '7\n'
    assert run(js, '(async () => { await null; return 9 })()')[1].text() == '9\n'
    assert run(js, 'Promise.resolve(1).then(v => console.log("then", v)); 2')[1].outputs == (
        StdoutOutput('then 1\n'),
        ResultOutput('2'),
    )

    result, sink = run(js, 'Promise.reject(new Error("bad"))')
    assert result.status is ResultStatus.ERROR
    assert sink.text().startswith('Uncaught (in promise) Error: bad')

    result, sink = run(js, 'new Promise(() => {})')
    assert result.ok
    assert sink.text() == 'Promise { <pending> }\n'


def test_a_given_context_is_used_as_is():
    ctx = quickjs.Context()
    ctx.eval('var shared = 1')
    js = QuickjsInterpreter(ctx)
    assert js.context is ctx
    assert run(js, 'shared + 1')[1].text() == '2\n'
    run(js, 'shared = 5')
    assert ctx.eval('shared') == 5


class _GatedExecutor(Executor):
    """Holds each run until released - to have two executions in flight at once."""

    def __init__(self):
        super().__init__()

        self.gate = asyncio.Event()

    async def run(self, fn, *, interrupt=None):
        await self.gate.wait()
        return fn()


@pytest.mark.asyncs('asyncio')
async def test_one_execution_at_a_time():
    executor = _GatedExecutor()
    js = QuickjsInterpreter(executor=executor)
    first = asyncio.ensure_future(js.execute('1', ListOutputSink()))
    await asyncio.sleep(0)
    with pytest.raises(InterpreterBusyError):
        await js.execute('2', ListOutputSink())
    executor.gate.set()
    assert (await first).ok
    assert (await js.execute('3', ListOutputSink())).ok


@pytest.mark.asyncs('asyncio')
async def test_threaded_evaluation_and_interruption():
    js = QuickjsInterpreter(executor=AsyncioThreadExecutor())
    sink = ListOutputSink()
    result = await js.execute('print("threaded"); 6 * 7', sink)
    assert result.ok
    assert sink.text() == 'threaded\n42\n'

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(js.execute('while (true) {}', ListOutputSink()), 1.)

    # The interrupt reached the engine: the context is free and usable again.
    await asyncio.sleep(.1)
    assert (await js.execute('1 + 1', sink)).ok
