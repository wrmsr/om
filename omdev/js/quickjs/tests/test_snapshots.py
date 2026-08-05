import pytest

from ... import quickjs
from ...quickjs import snapshots


##


def _restored(setup, *, ctx=None, **kwargs):
    src = quickjs.Context()
    src.eval(setup)
    snap = snapshots.take_snapshot(src, **kwargs)

    dst = ctx if ctx is not None else quickjs.Context()
    snapshots.restore_snapshot(dst, snap)
    return dst, snap


##


def test_pristine_baseline_is_excluded():
    ctx = quickjs.Context()
    assert snapshots.user_global_keys(ctx) == []
    # Whatever the engine defines on a fresh context is baseline, not user state.
    assert 'performance' in snapshots.pristine_global_keys()

    snap = snapshots.take_snapshot(ctx)
    assert snap.keys == []
    assert snap.skipped == {}


def test_round_trip():
    dst, snap = _restored(
        'globalThis.n = 1; globalThis.s = "x"; globalThis.o = {a: [1, 2]}; globalThis.d = new Date(5)',
    )

    assert sorted(snap.keys) == ['d', 'n', 'o', 's']
    assert dst.eval('n') == 1
    assert dst.eval('s') == 'x'
    assert dst.eval('o.a[1]') == 2
    assert dst.eval('d instanceof Date && d.getTime() === 5') is True
    assert dst.eval('performance !== undefined') is True  # baseline intact, not clobbered


def test_shared_references_between_globals_survive():
    dst, _ = _restored('var shared = {v: 1}; globalThis.a = {s: shared}; globalThis.b = {s: shared}')

    assert dst.eval('a.s === b.s') is True
    assert dst.eval('a.s === shared') is True


def test_restore_returns_names_and_overwrites():
    dst = quickjs.Context()
    dst.eval('globalThis.keep = "mine"; globalThis.n = "old"')

    src = quickjs.Context()
    src.eval('globalThis.n = "new"')
    names = snapshots.restore_snapshot(dst, snapshots.take_snapshot(src))

    assert names == ['n']
    assert dst.eval('n') == 'new'  # last write wins
    assert dst.eval('keep') == 'mine'  # untouched globals survive


def test_restore_accepts_raw_bytes():
    src = quickjs.Context()
    src.eval('globalThis.v = 42')
    blob = snapshots.take_snapshot(src).data
    assert isinstance(blob, bytes)

    dst = quickjs.Context()
    snapshots.restore_snapshot(dst, blob)
    assert dst.eval('v') == 42


def test_fanout_to_many_contexts():
    src = quickjs.Context()
    src.eval('globalThis.cfg = {mode: "test", items: [1, 2, 3]}')
    snap = snapshots.take_snapshot(src)

    for _ in range(4):
        dst = quickjs.Context()
        snapshots.restore_snapshot(dst, snap)
        assert dst.eval('cfg.items.length') == 3
        dst.eval('cfg.items.push(4)')  # clones are independent
        assert dst.eval('cfg.items.length') == 4
    assert src.eval('cfg.items.length') == 3


##


def test_unsupported_globals_raise_naming_keys():
    ctx = quickjs.Context()
    ctx.eval('globalThis.fn = function() {}; globalThis.p = Promise.resolve(1); globalThis.ok = 1')

    with pytest.raises(snapshots.UnsupportedGlobalsError) as exc_info:
        snapshots.take_snapshot(ctx)

    assert sorted(exc_info.value.reasons) == ['fn', 'p']
    assert 'fn' in str(exc_info.value)
    assert all(isinstance(r, str) and r for r in exc_info.value.reasons.values())


def test_python_callables_are_unsupported():
    ctx = quickjs.Context()
    ctx.set('py_fn', lambda: 1)

    with pytest.raises(snapshots.UnsupportedGlobalsError) as exc_info:
        snapshots.take_snapshot(ctx)
    assert list(exc_info.value.reasons) == ['py_fn']

    # Host objects must be re-registered after restoring, not carried in the snapshot.
    snap = snapshots.take_snapshot(ctx, skip_unsupported=True)
    dst = quickjs.Context()
    snapshots.restore_snapshot(dst, snap)
    assert dst.eval('typeof py_fn') == 'undefined'
    dst.set('py_fn', lambda: 1)
    assert dst.eval('py_fn()') == 1


def test_skip_unsupported_keeps_the_rest():
    dst, snap = _restored(
        'globalThis.fn = function() {}; globalThis.keep = {v: 1}; globalThis.n = 2',
        skip_unsupported=True,
    )

    assert sorted(snap.keys) == ['keep', 'n']
    assert list(snap.skipped) == ['fn']
    assert dst.eval('keep.v') == 1
    assert dst.eval('n') == 2
    assert dst.eval('typeof fn') == 'undefined'


##


# Each test below documents a real limitation inherited from the engine serializer. They assert today's actual
# behavior - if the engine ever improves, they fail loudly and should be updated (and TODO.md with them).


def test_limitation_prototypes_and_class_identity_lost():
    dst, _ = _restored('class Foo { constructor() { this.v = 1 } m() { return 2 } }; globalThis.inst = new Foo()')

    assert dst.eval('inst.v') == 1  # own data survives...
    assert dst.eval('typeof inst.m') == 'undefined'  # ...methods do not
    assert dst.eval('inst.constructor === Object') is True  # rehydrated as a plain object


def test_limitation_unique_symbol_identity_lost():
    dst, _ = _restored('var u = Symbol("uniq"); globalThis.holder = {sym: u, same: u}')

    assert dst.eval('typeof holder.sym') == 'symbol'
    assert dst.eval('String(holder.sym)') == 'Symbol(uniq)'  # description survives
    assert dst.eval('holder.sym === holder.same') is False  # ...but identity does not, even within one snapshot
    assert dst.eval('holder.sym === Symbol("uniq")') is False


def test_limitation_registered_symbols_reintern():
    dst, _ = _restored('globalThis.holder = {sym: Symbol.for("reg"), same: Symbol.for("reg")}')

    assert dst.eval('holder.sym === Symbol.for("reg")') is True
    assert dst.eval('holder.sym === holder.same') is True


def test_limitation_symbol_keyed_props_survive_but_unique_keys_are_unreachable():
    dst, _ = _restored('var u = Symbol("uniq"); globalThis.o = {[u]: "v", plain: 1}; globalThis.key = {u: u}')

    # The property itself is carried (contrary to what one might expect of a 'data only' format)...
    assert dst.eval('Object.getOwnPropertySymbols(o).length') == 1
    assert dst.eval('o[Object.getOwnPropertySymbols(o)[0]]') == 'v'
    # ...but its key symbol is a different symbol from the separately-restored one, so it cannot be looked up.
    assert dst.eval('o[key.u]') is None


def test_limitation_non_enumerable_props_dropped():
    dst, _ = _restored(
        'globalThis.o = {shown: 1}; Object.defineProperty(o, "hidden", {value: 2, enumerable: false})',
    )

    assert dst.eval('o.shown') == 1
    assert dst.eval('o.hidden') is None
    assert dst.eval('Object.keys(o).length') == 1


def test_limitation_nested_accessors_are_unsupported():
    ctx = quickjs.Context()
    ctx.eval('globalThis.o = {get g() { return 42 }, plain: 1}')

    with pytest.raises(snapshots.UnsupportedGlobalsError) as exc_info:
        snapshots.take_snapshot(ctx)
    assert list(exc_info.value.reasons) == ['o']


def test_limitation_global_accessors_captured_as_value():
    dst, _ = _restored(
        'Object.defineProperty(globalThis, "ga", {get() { return 7 }, enumerable: true, configurable: true})',
    )

    # Collecting globals reads them, so the getter's result is snapshotted as a plain value.
    assert dst.eval('ga') == 7
    assert dst.eval('Object.getOwnPropertyDescriptor(globalThis, "ga").get === undefined') is True


def test_limitation_builtin_mutations_invisible():
    dst, snap = _restored('Math.random = function() { return 0.5 }; globalThis.marker = 1')

    assert snap.keys == ['marker']  # Math is baseline, so its mutation is not user state
    assert dst.eval('Math.random() === 0.5') is False
    assert dst.eval('marker') == 1


def test_limitation_object_integrity_lost():
    dst, _ = _restored(
        'globalThis.f = Object.freeze({a: 1});'
        'globalThis.s = Object.seal({b: 1});'
        'globalThis.n = Object.preventExtensions({c: 1})',
    )

    assert dst.eval('Object.isFrozen(f)') is False
    assert dst.eval('Object.isSealed(s)') is False
    assert dst.eval('Object.isExtensible(n)') is True


def test_limitation_property_attributes_normalized():
    dst, _ = _restored(
        'globalThis.o = {};'
        'Object.defineProperty(o, "ro", {value: 1, writable: false, enumerable: true, configurable: false})',
    )

    assert dst.eval('o.ro') == 1
    assert dst.eval('Object.getOwnPropertyDescriptor(o, "ro").writable') is True
    assert dst.eval('Object.getOwnPropertyDescriptor(o, "ro").configurable') is True


def test_limitation_array_holes_and_extra_props():
    src = quickjs.Context()
    src.eval('globalThis.a = [1, , 3]; a.extra = "x"')
    assert src.eval('1 in a') is False

    dst = quickjs.Context()
    snapshots.restore_snapshot(dst, snapshots.take_snapshot(src))

    assert dst.eval('a.length') == 3
    assert dst.eval('1 in a') is True  # holes are filled in
    assert dst.eval('a[1]') is None
    assert dst.eval('a.extra') is None  # non-index array properties are dropped


def test_limitation_let_and_const_globals_not_captured():
    src = quickjs.Context()
    src.eval('var v = 1; let l = 2; const c = 3; globalThis.g = 4')

    # let/const live in the lexical scope, not on globalThis, so they are invisible to a snapshot.
    assert sorted(snapshots.user_global_keys(src)) == ['g', 'v']

    dst = quickjs.Context()
    snapshots.restore_snapshot(dst, snapshots.take_snapshot(src))
    assert dst.eval('v') == 1
    assert dst.eval('g') == 4
    assert dst.eval('typeof l') == 'undefined'
