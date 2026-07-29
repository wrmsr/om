import typing as ta

import pytest

from ... import inject as inj
from ... import lang


def test_override():
    i = inj.create_injector(
        inj.override(
            inj.bind(420),
            inj.bind(421),
        ),
        inj.bind(5.2),
        inj.bind(lang.typed_lambda(str, i=int, f=float)(lambda i, f: f'{i}, {f}')),
    )
    assert i.provide(int) == 421
    assert i.provide(str) == '421, 5.2'


def test_override_new_keys():
    i = inj.create_injector(
        inj.override(
            inj.as_elements(
                inj.bind(420),
                inj.bind(lang.typed_lambda(str, i=int, f=float)(lambda i, f: f'{i}, {f}')),
            ),
            inj.bind(421),
            inj.bind(5.2),
        ),
    )
    assert i.provide(int) == 421
    assert i.provide(float) == 5.2
    assert i.provide(str) == '421, 5.2'


##
# FIXME: override currently replaces per-key element lists wholesale - see TODO.md. The following tests encode the
# intended behaviors and are expected to fail until that is addressed.


@pytest.mark.xfail(reason='override replaces multi-bindings wholesale', strict=True)
def test_override_set_multi_merges():
    src = inj.as_elements(
        inj.bind(420, tag='a'),
        inj.set_binder[int]().bind(inj.as_key(int, tag='a')),

        inj.bind(421, tag='b'),
        inj.set_binder[int]().bind(inj.as_key(int, tag='b')),
    )
    ovr = inj.as_elements(
        inj.bind(422, tag='c'),
        inj.set_binder[int]().bind(inj.as_key(int, tag='c')),
    )

    i = inj.create_injector(inj.override(src, ovr))
    assert i.provide(ta.AbstractSet[int]) == {420, 421, 422}


@pytest.mark.xfail(reason='override replaces multi-bindings wholesale', strict=True)
def test_override_map_multi_merges():
    src = inj.as_elements(
        inj.bind(420, tag='a'),
        inj.map_binder[str, int]().bind('a', inj.as_key(int, tag='a')),

        inj.bind(421, tag='b'),
        inj.map_binder[str, int]().bind('b', inj.as_key(int, tag='b')),
    )
    ovr = inj.as_elements(
        inj.bind(422, tag='c'),
        inj.map_binder[str, int]().bind('c', inj.as_key(int, tag='c')),
    )

    i = inj.create_injector(inj.override(src, ovr))
    assert i.provide(ta.Mapping[str, int]) == {'a': 420, 'b': 421, 'c': 422}


@pytest.mark.xfail(reason='override drops src Eager elements alongside replaced bindings', strict=True)
def test_override_preserves_eager():
    cf = cg = 0

    def f() -> int:
        nonlocal cf
        cf += 1
        return 420

    def g() -> int:
        nonlocal cg
        cg += 1
        return 421

    i = inj.create_injector(
        inj.override(
            inj.bind(f, singleton=True, eager=True),
            inj.bind(g, singleton=True),
        ),
    )
    assert (cf, cg) == (0, 1)
    assert i.provide(int) == 421


@pytest.mark.xfail(reason='override replaces the non-keyed element bucket wholesale', strict=True)
def test_override_preserves_non_keyed_elements():
    ss = inj.SeededScope('hi')
    src = inj.as_elements(
        inj.bind_scope(ss),
        inj.bind(420, in_=ss),
        inj.bind('src'),
    )

    ls: list = []

    async def pl(i, key, binding, fn):
        ls.append(key)
        return await fn()

    ovr = inj.as_elements(
        inj.bind('ovr'),
        inj.bind_provision_listener(pl),
    )

    i = inj.create_injector(inj.override(src, ovr))
    assert i.provide(str) == 'ovr'
    with inj.enter_seeded_scope(i, ss, {}):
        assert i.provide(int) == 420
    assert ls
