import pytest

from ... import quickjs


##


def test_object_getitem():
    ctx = quickjs.Context()
    obj = ctx.eval('({a: 1, b: "x", c: null})')
    assert obj['a'] == 1
    assert obj['b'] == 'x'
    assert obj['c'] is None
    assert obj['missing'] is None


def test_object_setitem():
    ctx = quickjs.Context()
    obj = ctx.eval('globalThis.o = {}; o')
    obj['a'] = 5
    obj['b'] = {'nested': True}
    assert ctx.eval('o.a') == 5
    assert ctx.eval('o.b.nested') is True


def test_object_delitem():
    ctx = quickjs.Context()
    obj = ctx.eval('({a: 1, b: 2})')
    del obj['a']
    assert obj.keys() == ['b']


def test_object_key_types():
    ctx = quickjs.Context()
    arr = ctx.eval('[10, 20, 30]')
    assert arr[0] == 10
    assert arr[2] == 30
    assert arr['length'] == 3
    with pytest.raises(TypeError):
        arr[1.5]


def test_object_keys():
    ctx = quickjs.Context()
    assert ctx.eval('({a: 1, b: 2})').keys() == ['a', 'b']
    assert ctx.eval('({})').keys() == []


def test_function_call():
    ctx = quickjs.Context()
    f = ctx.eval('(x, y) => x + y')
    assert f(1, 2) == 3
    assert f('a', 'b') == 'ab'


def test_function_call_no_kwargs():
    ctx = quickjs.Context()
    f = ctx.eval('x => x')
    with pytest.raises(TypeError):
        f(x=1)


def test_call_non_function_raises():
    ctx = quickjs.Context()
    obj = ctx.eval('({})')
    with pytest.raises(quickjs.JsError):
        obj()


def test_invoke():
    ctx = quickjs.Context()
    obj = ctx.eval('({v: 10, add(n) { return this.v + n; }})')
    assert obj.invoke('add', 5) == 15
    with pytest.raises(quickjs.JsError):
        obj.invoke('missing')
    with pytest.raises(TypeError):
        obj.invoke()


def test_json():
    ctx = quickjs.Context()
    assert ctx.eval('({a: [1, 2]})').json() == '{"a":[1,2]}'
    # Functions are not JSON-serializable: JSON.stringify yields undefined.
    assert ctx.eval('(() => 1)').json() is None


def test_str():
    ctx = quickjs.Context()
    assert str(ctx.eval('({})')) == '[object Object]'
    assert str(ctx.eval('[1, 2]')) == '1,2'


def test_global_this():
    ctx = quickjs.Context()
    g = ctx.global_this
    assert isinstance(g, quickjs.Object)
    g['fromPython'] = 123
    assert ctx.eval('fromPython') == 123
    assert g['Math'].invoke('abs', -5) == 5


def test_object_not_instantiable():
    with pytest.raises(TypeError):
        quickjs.Object()


def test_object_identity_preserved():
    ctx = quickjs.Context()
    obj = ctx.eval('globalThis.ident = {}; ident')
    ctx.set('same', obj)
    assert ctx.eval('same === ident') is True


def test_getter_runs_js():
    ctx = quickjs.Context()
    obj = ctx.eval('({get prop() { return 41 + 1; }})')
    assert obj['prop'] == 42


def test_getter_error_propagates():
    ctx = quickjs.Context()
    obj = ctx.eval('({get prop() { throw new Error("getter boom"); }})')
    with pytest.raises(quickjs.JsError, match='getter boom'):
        obj['prop']


def test_symbol_wrapped():
    ctx = quickjs.Context()
    sym = ctx.eval('Symbol("s")')
    assert isinstance(sym, quickjs.Object)
