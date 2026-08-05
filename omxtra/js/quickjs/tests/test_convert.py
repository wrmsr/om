import json

import pytest

from ... import quickjs


##


def test_set_scalars():
    ctx = quickjs.Context()
    for name, value in [
        ('a', None),
        ('b', True),
        ('c', 7),
        ('d', 2.5),
        ('e', 'hi'),
    ]:
        ctx.set(name, value)
    assert ctx.eval('a') is None
    assert ctx.eval('b') is True
    assert ctx.eval('c') == 7
    assert ctx.eval('d') == 2.5
    assert ctx.eval('e') == 'hi'


def test_set_int_ranges():
    ctx = quickjs.Context()

    ctx.set('small', 2 ** 31 - 1)
    assert ctx.eval('typeof small') == 'number'
    assert ctx.eval('small') == 2 ** 31 - 1

    ctx.set('mid', 2 ** 53)
    assert ctx.eval('typeof mid') == 'number'
    assert ctx.eval('mid') == 2 ** 53

    ctx.set('big', 2 ** 53 + 1)
    assert ctx.eval('typeof big') == 'bigint'
    assert ctx.eval('big') == 2 ** 53 + 1

    ctx.set('huge', 10 ** 30)
    assert ctx.eval('typeof huge') == 'bigint'
    assert ctx.eval('huge') == 10 ** 30
    ctx.set('neg_huge', -(10 ** 30))
    assert ctx.eval('neg_huge') == -(10 ** 30)


def test_set_containers():
    ctx = quickjs.Context()
    data = {'a': [1, 2.5, 'x', None, True], 'b': {'nested': [{'deep': 1}]}}
    ctx.set('data', data)
    assert ctx.eval('Array.isArray(data.a)') is True
    assert json.loads(ctx.get('data').json()) == data


def test_set_tuple():
    ctx = quickjs.Context()
    ctx.set('t', (1, 2, 3))
    assert ctx.eval('Array.isArray(t) && t.length === 3 && t[2] === 3') is True


def test_set_bytes():
    ctx = quickjs.Context()
    ctx.set('buf', b'\x01\x02\x03')
    assert ctx.eval('buf instanceof Uint8Array') is True
    assert ctx.eval('buf.length') == 3
    assert ctx.eval('buf[1]') == 2

    ctx.set('barr', bytearray(b'xy'))
    assert ctx.eval('barr instanceof Uint8Array && barr.length === 2') is True


def test_to_bytes():
    ctx = quickjs.Context()
    assert ctx.eval('new Uint8Array([1, 2, 3])').to_bytes() == b'\x01\x02\x03'
    assert ctx.eval('new Uint8Array([255]).buffer').to_bytes() == b'\xff'
    with pytest.raises(quickjs.JsError):
        ctx.eval('({})').to_bytes()


def test_set_dict_key_type():
    ctx = quickjs.Context()
    with pytest.raises(TypeError):
        ctx.set('x', {1: 'a'})  # type: ignore[dict-item]  # deliberately invalid


def test_set_unsupported_type():
    ctx = quickjs.Context()
    with pytest.raises(TypeError):
        ctx.set('x', object())  # type: ignore[arg-type]  # deliberately invalid


def test_set_object_roundtrip():
    ctx = quickjs.Context()
    obj = ctx.eval('({v: 1})')
    ctx.set('alias', obj)
    assert ctx.eval('alias.v') == 1
    ctx.eval('alias.v = 2')
    assert obj['v'] == 2


def test_cross_context_object_rejected():
    ctx1 = quickjs.Context()
    ctx2 = quickjs.Context()
    obj = ctx1.eval('({})')
    with pytest.raises(ValueError):  # noqa
        ctx2.set('x', obj)


def test_nesting_depth_limit():
    ctx = quickjs.Context()
    deep: list = []
    for _ in range(100):
        deep = [deep]
    with pytest.raises(ValueError):  # noqa
        ctx.set('deep', deep)


def test_float_specials_roundtrip():
    ctx = quickjs.Context()
    ctx.set('inf', float('inf'))
    assert ctx.eval('inf === Infinity') is True
    ctx.set('nan', float('nan'))
    assert ctx.eval('Number.isNaN(nan)') is True
