import pytest

from ... import quickjs


##


def test_simple_callable():
    ctx = quickjs.Context()
    ctx.set('f', lambda: 42)
    assert ctx.eval('typeof f') == 'function'
    assert ctx.eval('f()') == 42


def test_callable_args_roundtrip():
    ctx = quickjs.Context()
    seen = []

    def record(*args):
        seen.append(args)
        return len(args)

    ctx.set('record', record)
    assert ctx.eval('record(1, "a", null, true, 2.5)') == 5
    assert seen == [(1, 'a', None, True, 2.5)]


def test_callable_name():
    ctx = quickjs.Context()

    def my_function():
        return None

    ctx.set('g', my_function)
    assert ctx.eval('g.name') == 'my_function'


def test_callable_returning_container():
    ctx = quickjs.Context()
    ctx.set('make', lambda: {'a': [1, 2]})
    assert ctx.eval('make().a[1]') == 2


def test_callable_receiving_js_object():
    ctx = quickjs.Context()
    ctx.set('extract', lambda obj: obj['k'])
    assert ctx.eval('extract({k: 9})') == 9


def test_python_exception_propagates():
    ctx = quickjs.Context()

    def boom():
        raise ValueError('boom')

    ctx.set('boom', boom)
    with pytest.raises(ValueError, match='boom'):
        ctx.eval('boom()')


def test_python_exception_identity():
    ctx = quickjs.Context()
    marker = KeyError('unique-marker')

    def boom():
        raise marker

    ctx.set('boom', boom)
    with pytest.raises(KeyError) as exc_info:
        ctx.eval('boom()')
    assert exc_info.value is marker


def test_js_can_catch_python_error():
    ctx = quickjs.Context()

    def boom():
        raise ValueError('inner detail')

    ctx.set('boom', boom)
    result = ctx.eval('(() => { try { boom(); return "no throw"; } catch (e) { return e.message; } })()')
    assert 'ValueError' in result
    assert 'inner detail' in result


def test_js_rethrows_own_error():
    ctx = quickjs.Context()

    def boom():
        raise ValueError('inner')

    ctx.set('boom', boom)
    with pytest.raises(quickjs.JsError, match='wrapped'):
        ctx.eval('(() => { try { boom(); } catch (e) { throw new Error("wrapped"); } })()')


def test_unconvertible_return_raises():
    ctx = quickjs.Context()
    ctx.set('bad', lambda: object())
    with pytest.raises(TypeError):
        ctx.eval('bad()')


def test_reentrant_eval():
    ctx = quickjs.Context()
    ctx.set('nest', lambda: ctx.eval('6 * 7'))
    assert ctx.eval('nest()') == 42


def test_reentrant_js_function_call():
    ctx = quickjs.Context()
    double = ctx.eval('x => x * 2')
    ctx.set('via_python', lambda x: double(x))
    assert ctx.eval('via_python(21)') == 42


def test_callable_as_js_callback():
    ctx = quickjs.Context()
    # Array.prototype.map invokes the callback with (value, index, array).
    ctx.set('double', lambda x, *_: x * 2)
    assert ctx.eval('[1, 2, 3].map(double)').json() == '[2,4,6]'
