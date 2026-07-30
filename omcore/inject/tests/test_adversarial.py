"""
Adversarial tests: hostile graph shapes, failure paths, aliasing subtleties, and API misuse, codifying exactly what
the injector does under each. Concurrency-flavored adversarials (racing singletons, cross-context cycles, context
residue) live in test_concurrency.py; override semantics in test_overrides.py.
"""
import typing as ta

import pytest

from ... import inject as inj


##
# Graph shapes.


def test_deep_link_chain():
    # A 200-deep link chain resolves. (The provision machinery is recursive - chains a few hundred deep are fine, but
    # somewhere past ~500 lies RecursionError. Real graphs are nowhere near; this pins the supported ballpark.)
    n = 200
    els: list[inj.Elemental] = [inj.bind(420, tag=n)]
    for k in range(n):
        els.append(inj.bind(inj.as_key(int, tag=k), to_key=inj.as_key(int, tag=k + 1)))

    assert inj.create_injector(*els)[inj.as_key(int, tag=0)] == 420


def test_wide_fanout_shares_one_request():
    # Thirty sibling providers under one bound root, all pulling one unscoped dependency, resolved in a single
    # request: one construction, shared by all.
    made: list = []

    class Dep:
        def __init__(self) -> None:
            made.append(self)

    els: list[inj.Elemental] = [inj.bind(Dep)]
    keys = {}
    for k in range(30):
        keys[f'a{k}'] = inj.as_key(object, tag=k)
        els.append(inj.bind(inj.as_key(object, tag=k), to_fn=inj.target(d=Dep)(lambda d: d)))
    els.append(inj.bind(list, to_fn=inj.KwargsTarget.of(lambda **kw: list(kw.values()), **keys)))

    i = inj.create_injector(*els)
    vs = i[list]

    assert len(made) == 1
    assert all(v is made[0] for v in vs)


def test_top_level_inject_shares_one_request():
    # Top-level `inject` / `provide_kwargs` runs under a single request, just like a bound root - sibling parameters
    # share unscoped provisions. (This once resolved each parameter as its own request - pinned against regression.)
    made: list = []

    class Dep:
        def __init__(self) -> None:
            made.append(self)

    els: list[inj.Elemental] = [inj.bind(Dep)]
    keys = {}
    for k in range(3):
        keys[f'a{k}'] = inj.as_key(object, tag=k)
        els.append(inj.bind(inj.as_key(object, tag=k), to_fn=inj.target(d=Dep)(lambda d: d)))

    i = inj.create_injector(*els)
    i.inject(inj.KwargsTarget.of(lambda **kw: None, **keys))
    assert len(made) == 1

    # The injected call itself is inside the request too - a constructor reentrantly using an injected Injector
    # joins it and sees the same memoized provisions its sibling parameters got:
    class Reentrant:
        def __init__(self, i: inj.Injector, a0: ta.Annotated[object, inj.Tag(0)]) -> None:
            self.a0 = a0
            self.a1 = i.provide(inj.as_key(object, tag=1))

    made.clear()
    r = inj.create_injector(*els).inject(Reentrant)
    assert len(made) == 1
    assert r.a0 is r.a1


def test_self_cycle():
    def f(x: int) -> int:
        return x + 1

    i = inj.create_injector(inj.bind(f))
    with pytest.raises(inj.CyclicDependencyError):
        i.provide(int)


def test_link_cycle():
    i = inj.create_injector(
        inj.bind(inj.as_key(int, tag='a'), to_key=inj.as_key(int, tag='b')),
        inj.bind(inj.as_key(int, tag='b'), to_key=inj.as_key(int, tag='a')),
    )
    with pytest.raises(inj.CyclicDependencyError):
        i.provide(inj.as_key(int, tag='a'))


def test_reentrant_provide_joins_the_request():
    # A provider that calls back into the injector mid-provision joins the in-flight request - reentrant provisions
    # see the same memoized instances as the request that spawned them.
    class Leaf:
        pass

    def side(leaf: Leaf) -> tuple:
        return ('side', leaf)

    def main(i: inj.Injector, leaf: Leaf) -> list:
        return [leaf, i.provide(tuple)[1]]

    i = inj.create_injector(inj.bind(Leaf), inj.bind(side), inj.bind(main))
    a, b = i[list]
    assert a is b


##
# Failure paths.


def test_singleton_failure_is_not_cached():
    calls: list = []

    def flaky() -> int:
        calls.append(None)
        if len(calls) == 1:
            raise ValueError('first time hurts')
        return 420

    i = inj.create_injector(inj.bind(flaky, singleton=True))

    with pytest.raises(ValueError, match='first time hurts'):
        i.provide(int)

    # The failure was not cached as the singleton value - the next provision retries:
    assert i.provide(int) == 420
    assert i.provide(int) == 420
    assert len(calls) == 2


def test_eager_failure_fails_creation():
    # Eager singletons fail fast: a broken one surfaces its original error from create_injector itself.
    def broken() -> int:
        raise ValueError('boom')

    with pytest.raises(ValueError, match='boom'):
        inj.create_injector(inj.bind(broken, singleton=True, eager=True))


def test_none_is_a_value():
    # A provider returning None is a successful provision, distinct from unbound:
    i = inj.create_injector(inj.bind(object, to_fn=lambda: None))

    mv = i.try_provide(object)
    assert mv.present
    assert mv.must() is None
    assert i.provide(object) is None


##
# Scope abuse.


def test_delimited_scope_reentry_rejected():
    ss = inj.DelimitedScope('once')
    i = inj.create_injector(inj.bind_scope(ss))

    with inj.enter_scope(i, ss, {}):
        with pytest.raises(inj.ScopeAlreadyOpenError):  # noqa
            with inj.enter_scope(i, ss, {}):
                pass


def test_missing_seed():
    # Entering a scope without a declared seed is not itself an error - but providing that seed key surfaces a raw
    # KeyError from the seed map. (A candidate for a friendlier error, like the unregistered-scope KeyError in
    # TODO.md.)
    ss = inj.DelimitedScope('underfed')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
    )

    with inj.enter_scope(i, ss, {}):
        with pytest.raises(KeyError):
            i.provide(float)


def test_singleton_captures_first_scope_value():
    # Footgun, codified: a *singleton* depending on a scope-seeded value is constructed at first provision and then
    # outlives the scope - later openings see the first opening's capture. Scope-dependent state belongs in the scope.
    class Sticky:
        def __init__(self, f: float) -> None:
            self.f = f

    ss = inj.DelimitedScope('sticky')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.bind(Sticky, singleton=True),
    )

    with inj.enter_scope(i, ss, {inj.as_key(float): 1.0}):
        first = i[Sticky]
        assert first.f == 1.0

    with inj.enter_scope(i, ss, {inj.as_key(float): 2.0}):
        assert i[Sticky] is first
        assert i[Sticky].f == 1.0  # not 2.0!


def test_overlapping_scope_lifetimes():
    # Delimited scopes are independent: their lifetimes may overlap without nesting. (Iceworm's staggered phase scopes
    # relied on exactly this - a 'post' scope opening before the prior phase's scopes close, and outliving them.)
    a = inj.DelimitedScope('a')
    b = inj.DelimitedScope('b')
    i = inj.create_injector(
        inj.bind_scope(a),
        inj.bind_scope(b),
        inj.bind(420, in_=a),
        inj.bind('yo', in_=b),
    )

    cma = inj.enter_scope(i, a, {})
    cmb = inj.enter_scope(i, b, {})

    a_open = b_open = False
    try:
        cma.__enter__()
        a_open = True
        assert i[int] == 420

        cmb.__enter__()
        b_open = True

        cma.__exit__(None, None, None)  # a closes first - non-LIFO
        a_open = False

        assert i[str] == 'yo'
        with pytest.raises(inj.ScopeNotOpenError):
            i.provide(int)
    finally:
        if a_open:
            cma.__exit__(None, None, None)
        if b_open:
            cmb.__exit__(None, None, None)


def test_child_injector_shadowing():
    # Keys bound in a child shadow the parent's; unbound keys fall through. (TODO.md contemplates restricting
    # shadowing of parent bindings - this pins the current, documented-as-intended behavior.)
    parent = inj.create_injector(inj.bind('app'), inj.bind(420))
    child = inj.create_injector(inj.collect_elements(inj.as_elements(inj.bind('child'))), parent=parent)

    assert child[str] == 'child'
    assert child[int] == 420
    assert parent[str] == 'app'


##
# Multis under pressure.


def test_scoped_multi_aggregate():
    # The set *aggregate* binding is unscoped by default - each provision builds a fresh set (of freshly-provided
    # entries). Manually binding the aggregate as a singleton caches the whole collection, entries included.
    class Item:
        pass

    sk = inj.as_key(ta.AbstractSet[Item])

    fresh = inj.create_injector(
        inj.bind(Item, tag=1),
        inj.bind(Item, tag=2),
        inj.set_binder[Item]().bind(inj.as_key(Item, tag=1), inj.as_key(Item, tag=2)),
    )
    assert fresh[sk] is not fresh[sk]

    cached = inj.create_injector(
        inj.bind(Item, tag=1),
        inj.bind(Item, tag=2),
        inj.bind(sk, to_provider=inj.SetProvider(sk), singleton=True),
        inj.SetBinding(sk, inj.as_key(Item, tag=1)),
        inj.SetBinding(sk, inj.as_key(Item, tag=2)),
    )
    s = cached[sk]
    assert cached[sk] is s
    assert len(s) == 2


def test_unhashable_set_entries_raise():
    # Set multibinding entries must be hashable - contributing an unhashable value dies at provision. (This is why
    # ItemsBinderHelper boxes contributed item sequences; see helpers/multis.py.)
    i = inj.create_injector(
        inj.set_binder[list](),
        inj.bind_set_entry_const(ta.AbstractSet[list], [1, 2]),
    )
    with pytest.raises(TypeError):
        i.provide(ta.AbstractSet[list])


def test_override_replaces_exposed_private_key():
    # Keys exposed from a private participate in override like any other key:
    i = inj.create_injector(inj.override(
        inj.private(inj.bind(420, expose=True)),
        inj.bind(421),
    ))
    assert i[int] == 421


##
# API misuse - the front door rejects nonsense loudly.


def test_bind_rejections():
    with pytest.raises(TypeError):
        inj.bind(None)

    with pytest.raises(TypeError):
        inj.bind(inj.bind(420))  # elements are not bindable values

    with pytest.raises(TypeError):
        inj.bind(int, to_const=420, to_fn=lambda: 421)  # at most one provider

    with pytest.raises(TypeError):
        inj.bind(inj.as_key(int))  # a bare key needs an explicit provider

    with pytest.raises(TypeError):
        inj.bind(420, in_=inj.ThreadScope(), singleton=True)  # at most one scope

    with pytest.raises(TypeError):
        inj.bind(inj.as_key(int, tag='a'), tag='b', to_const=420)  # tag already set

    with pytest.raises(TypeError):
        inj.as_key(inj.as_key(int), tag='a')  # ditto


def test_key_equality():
    assert inj.as_key(int) == inj.as_key(int, tag=None)  # None tag is 'no tag'
    assert hash(inj.as_key(int)) == hash(inj.as_key(int, tag=None))
    assert inj.as_key(int) != inj.as_key(int, tag='a')
    assert inj.as_key(int) != inj.as_key(bool)


def test_empty_element_sets():
    # An empty module is legal, composes, and can even be the whole graph:
    i = inj.create_injector(inj.as_elements(), inj.as_elements(inj.as_elements()))
    assert not i.try_provide(int).present


def test_degenerate_override():
    # `override(src)` with nothing overriding is valid and identity-ish - real binders leave these as placeholders:
    es = inj.override(inj.as_elements(inj.bind(420)))
    assert inj.create_injector(es)[int] == 420


def test_elements_are_iterable():
    # `Elements` is iterable - real binders sometimes `extend` an accumulator with one rather than appending it:
    els: list = []
    els.extend(inj.as_elements(inj.bind(420), inj.bind('yo')))
    assert len(els) == 2
    assert inj.create_injector(*els)[int] == 420
