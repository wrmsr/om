import pytest

from ... import quickjs


##


def _roundtrip(ctx, code):
    blob = ctx.eval(code).serialize()
    assert isinstance(blob, bytes)
    ctx.set('r', ctx.deserialize(blob))


def test_roundtrip_basics():
    ctx = quickjs.Context()
    _roundtrip(ctx, '({a: 1, s: "x", f: 1.5, n: null, arr: [1, 2, 3], big: 2n ** 70n})')
    assert ctx.eval('r.a === 1 && r.s === "x" && r.f === 1.5 && r.n === null') is True
    assert ctx.eval('Array.isArray(r.arr) && r.arr.length === 3 && r.arr[2] === 3') is True
    assert ctx.eval('r.big === 2n ** 70n') is True


def test_roundtrip_shared_refs_and_cycles():
    ctx = quickjs.Context()
    _roundtrip(ctx, '(function() { var s = {v: 1}; var o = {x: s, y: {v: 2}, x2: s}; o.self = o; return o; })()')
    assert ctx.eval('r.x2 === r.x') is True
    assert ctx.eval('r.x2 !== r.y') is True
    assert ctx.eval('r.self === r') is True


def test_roundtrip_builtins():
    ctx = quickjs.Context()
    _roundtrip(ctx, '({m: new Map([[1, "a"]]), s: new Set([1, 2]), d: new Date(1234567890123)})')
    assert ctx.eval('r.m instanceof Map && r.m.get(1) === "a"') is True
    assert ctx.eval('r.s instanceof Set && r.s.has(2)') is True
    assert ctx.eval('r.d instanceof Date && r.d.getTime() === 1234567890123') is True


def test_roundtrip_regexp_alone():
    ctx = quickjs.Context()
    _roundtrip(ctx, '({re: /ab+c/gi})')
    assert ctx.eval('r.re instanceof RegExp && r.re.source === "ab+c" && r.re.flags === "gi"') is True
    assert ctx.eval('r.re.test("xABBc")') is True


def test_roundtrip_typed_arrays():
    ctx = quickjs.Context()
    _roundtrip(
        ctx,
        '({buf: new Uint8Array([1, 2, 3]).buffer, u8: new Uint8Array([4, 5]), f64: new Float64Array([1.5, -2.5])})',
    )
    assert ctx.eval('r.buf instanceof ArrayBuffer && r.buf.byteLength === 3') is True
    assert ctx.eval('r.u8 instanceof Uint8Array && r.u8.length === 2') is True
    assert ctx.eval('r.f64 instanceof Float64Array && r.f64[0] === 1.5 && r.f64[1] === -2.5') is True
    assert ctx.eval('r.u8').to_bytes() == b'\x04\x05'


def test_roundtrip_aliased_views():
    ctx = quickjs.Context()
    _roundtrip(
        ctx,
        '(function() { var b = new Uint8Array([1, 2, 3, 4]).buffer; return {u8: new Uint8Array(b), u16: new Uint16Array(b)}; })()',  # noqa: E501
    )
    assert ctx.eval('r.u8.buffer === r.u16.buffer') is True
    # A write through one view is visible through the other - the backing buffer is genuinely shared.
    assert ctx.eval('(function() { var before = r.u16[0]; r.u8[0] = 99; return r.u16[0] !== before; })()') is True


def test_unserializable_raises():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError):
        ctx.eval('(function f() { return 1; })').serialize()
    with pytest.raises(quickjs.JsError):
        ctx.eval('Promise.resolve(1)').serialize()


def test_accessor_property_raises():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError):
        ctx.eval('({get x() { return 1; }})').serialize()


def test_deserialize_garbage_raises():
    ctx = quickjs.Context()
    with pytest.raises(quickjs.JsError):
        ctx.deserialize(b'\xffgarbage')

    blob = ctx.eval('({a: 1})').serialize()
    with pytest.raises(quickjs.JsError):
        ctx.deserialize(bytes([blob[0] ^ 0xff]) + blob[1:])  # corrupt the BC_VERSION byte


# Regression tests for an upstream bug (present through quickjs-ng 0.16.1, patched locally in _quickjs - see the
# @om-local-patch in JS_ReadRegExp): the writer registers every object - RegExps included - in its reference table
# before dispatch, but JS_ReadRegExp did not register the rebuilt RegExp on the read side, so back-references to
# objects following a RegExp in the stream resolved against a shifted index space - silently yielding the wrong
# object, or erroring with 'invalid object reference'.


def test_shared_ref_after_regexp():
    ctx = quickjs.Context()
    _roundtrip(ctx, '(function() { var s = {v: 1}; return {re: /a/, x: s, y: {v: 2}, x2: s}; })()')
    assert ctx.eval('r.x2 === r.x') is True
    assert ctx.eval('r.x2 !== r.y') is True


def test_aliased_regexp():
    ctx = quickjs.Context()
    _roundtrip(ctx, '(function() { var re = /a/; return {re: re, re2: re}; })()')
    assert ctx.eval('r.re2 === r.re') is True
    assert ctx.eval('r.re2 instanceof RegExp') is True
