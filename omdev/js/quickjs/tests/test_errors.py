import pytest

from ... import quickjs


##


def test_error_hierarchy():
    assert issubclass(quickjs.JsStackOverflowError, quickjs.JsError)
    assert issubclass(quickjs.JsInterruptError, quickjs.JsError)


def test_throw_error():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError) as exc_info:
        ctx.eval('throw new Error("nope")')
    assert 'nope' in str(exc_info.value)
    assert isinstance(exc_info.value.js_stack, str)


def test_stack_attribute():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError) as exc_info:
        ctx.eval('function inner() { throw new TypeError("t"); }\ninner()')
    assert 'inner' in (exc_info.value.js_stack or '')


def test_throw_non_error():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError) as exc_info:
        ctx.eval('throw 42')
    assert '42' in str(exc_info.value)
    assert exc_info.value.js_stack is None


def test_syntax_error():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError, match='[Ss]yntax'):  # noqa
        ctx.eval('this is not js')


def test_reference_error():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError, match='not defined'):
        ctx.eval('definitely_not_defined()')


def test_stack_overflow():
    ctx = quickjs.Context()
    ctx.set_max_stack_size(256 * 1024)
    with pytest.raises(quickjs.JsStackOverflowError):
        ctx.eval('function r() { return r(); } r()')
    # The context remains usable afterwards.
    assert ctx.eval('1 + 1') == 2


def test_error_caught_in_js_not_raised():
    ctx = quickjs.Context()
    assert ctx.eval('(() => { try { nope(); } catch (e) { return "ok"; } })()') == 'ok'
