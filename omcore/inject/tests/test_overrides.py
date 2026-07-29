import typing as ta

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
# Overrides operate on keys: per-key element buckets replace wholesale, all element kinds alike - an override binding
# a key is the entire story for that key. Non-keyed elements (scope bindings, provision listeners) concatenate - with
# no key, there is nothing to override. Additive intent is instead expressed by composing outside the override:
# `as_elements` appends, so new multi entries or Eagers are added as siblings of the override.


def test_override_replaces_set_multi():
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
    assert i.provide(ta.AbstractSet[int]) == {422}


def test_override_replaces_map_multi():
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
    assert i.provide(ta.Mapping[str, int]) == {'c': 422}


def test_override_then_append_set_multi():
    src = inj.as_elements(
        inj.bind('bar'),

        inj.bind(420, tag='a'),
        inj.set_binder[int]().bind(inj.as_key(int, tag='a')),

        inj.bind(421, tag='b'),
        inj.set_binder[int]().bind(inj.as_key(int, tag='b')),
    )

    i = inj.create_injector(
        inj.override(src, inj.bind('foo')),

        inj.bind(422, tag='c'),
        inj.set_binder[int]().bind(inj.as_key(int, tag='c')),
    )
    assert i.provide(str) == 'foo'
    assert i.provide(ta.AbstractSet[int]) == {420, 421, 422}


def test_override_replaces_eager():
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
    assert (cf, cg) == (0, 0)
    assert i.provide(int) == 421
    assert (cf, cg) == (0, 1)

    cf = cg = 0
    inj.create_injector(
        inj.override(
            inj.bind(f, singleton=True, eager=True),
            inj.bind(g, singleton=True, eager=True),
        ),
    )
    assert (cf, cg) == (0, 1)


def test_override_then_append_eager():
    cf = cg = 0

    def f() -> int:
        nonlocal cf
        cf += 1
        return 420

    def g() -> int:
        nonlocal cg
        cg += 1
        return 421

    inj.create_injector(
        inj.override(
            inj.bind(f, singleton=True, eager=True),
            inj.bind(g, singleton=True),
        ),
        inj.Eager(inj.as_key(int)),
    )
    assert (cf, cg) == (0, 1)


def test_override_concats_non_keyed():
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
