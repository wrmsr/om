import math

import pytest

from ... import quickjs


##


def test_version():
    assert isinstance(quickjs.QJS_VERSION, str)
    assert quickjs.QJS_VERSION


def test_eval_primitives():
    ctx = quickjs.Context()
    assert ctx.eval('1 + 2') == 3
    assert ctx.eval('1.5 * 2') == 3.0
    assert ctx.eval('"a" + "b"') == 'ab'
    assert ctx.eval('true') is True
    assert ctx.eval('false') is False
    assert ctx.eval('null') is None
    assert ctx.eval('undefined') is None


def test_eval_number_types():
    ctx = quickjs.Context()
    assert isinstance(ctx.eval('1 + 1'), int)
    assert isinstance(ctx.eval('0.5 + 0.5'), float)
    assert math.isnan(ctx.eval('NaN'))
    assert ctx.eval('Infinity') == math.inf


def test_eval_bigint():
    ctx = quickjs.Context()
    assert ctx.eval('123456789012345678901234567890n') == 123456789012345678901234567890
    assert ctx.eval('2n ** 100n') == 2 ** 100
    assert ctx.eval('-42n') == -42


def test_eval_unicode():
    ctx = quickjs.Context()
    assert ctx.eval('"héllo \\u00e9 🎉"') == 'héllo é 🎉'
    assert ctx.eval('"a\\u0000b"') == 'a\x00b'


def test_eval_strict():
    ctx = quickjs.Context()
    ctx.eval('y = 2')
    with pytest.raises(quickjs.JsError):
        ctx.eval('x = 1', strict=True)


def test_eval_filename():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError) as exc_info:
        ctx.eval('throw new Error("nope")', filename='myfile.js')
    assert 'myfile.js' in exc_info.value.js_stack


def test_eval_state_persists():
    ctx = quickjs.Context()
    ctx.eval('let counter = 10')
    ctx.eval('counter += 5')
    assert ctx.eval('counter') == 15


def test_contexts_are_isolated():
    ctx1 = quickjs.Context()
    ctx2 = quickjs.Context()
    ctx1.eval('globalThis.v = 1')
    assert ctx2.eval('globalThis.v') is None


def test_get_and_set_globals():
    ctx = quickjs.Context()
    ctx.set('x', 42)
    assert ctx.eval('x') == 42
    assert ctx.get('x') == 42
    assert ctx.get('missing') is None


def test_parse_json():
    ctx = quickjs.Context()
    assert ctx.parse_json('123') == 123
    obj = ctx.parse_json('{"a": [1, 2, {"b": "c"}]}')
    assert obj['a'][2]['b'] == 'c'
    with pytest.raises(quickjs.JsError):
        ctx.parse_json('{nope}')
