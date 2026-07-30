"""
Reference-cycle hygiene tests: the injector's own machinery must not require the cyclic garbage collector.
Steady-state provision must produce zero cyclic garbage, and dropped injectors must be reclaimed by pure refcounting
alone - modulo deliberately-cyclic user graphs (a singleton injecting the Injector itself is its own antipattern).
"""
import contextlib
import gc
import weakref

import pytest

from ... import inject as inj
from ... import lang


##


@contextlib.contextmanager
def _no_gc():
    was = gc.isenabled()
    gc.collect()
    gc.disable()
    try:
        yield
    finally:
        if was:
            gc.enable()


class Leaf:
    pass


class Holder:
    def __init__(self, leaf: Leaf) -> None:
        self.leaf = leaf


SCOPE = inj.SeededScope('gc-req')


##


def test_injector_collects_without_gc():
    with _no_gc():
        i = inj.create_injector(
            inj.bind(Leaf),
            inj.bind(Holder, singleton=True),
        )
        i[Holder]

        refs = (weakref.ref(i), weakref.ref(i[inj.AsyncInjector]))
        del i
        assert all(r() is None for r in refs)


def test_async_injector_collects_without_gc():
    with _no_gc():
        ai = lang.sync_await(inj.create_async_injector(inj.bind(Leaf)))
        lang.sync_await(ai.provide(Leaf))

        r = weakref.ref(ai)
        del ai
        assert r() is None


def test_child_injectors_collect_without_gc():
    # The child-injector-per-request pattern: with the element collection reused across children, each child must be
    # reclaimed by refcount at drop - no per-request cyclic garbage.
    with _no_gc():
        parent = inj.create_injector(inj.bind(Holder, singleton=True), inj.bind(Leaf))
        ce = inj.collect_elements(inj.as_elements(inj.bind(Leaf)))

        for _ in range(3):
            c = inj.create_injector(ce, parent=parent)
            c.provide(Leaf)

            refs = (weakref.ref(c), weakref.ref(c[inj.AsyncInjector]))
            del c
            assert all(r() is None for r in refs)

        pr = weakref.ref(parent)
        del parent
        assert pr() is None


def test_seeded_scope_injector_collects_without_gc():
    # Exercises the seeded-scope Manager (singleton-cached, holding its injector weakly) before dropping.
    with _no_gc():
        i = inj.create_injector(
            inj.bind_scope(SCOPE),
            inj.bind_scope_seed(float, SCOPE),
            inj.bind(420, in_=SCOPE),
        )
        for f in (1.0, 2.0):
            with inj.enter_seeded_scope(i, SCOPE, {inj.as_key(float): f}):
                assert i[int] == 420
                assert i[float] == f

        refs = (weakref.ref(i), weakref.ref(i[inj.AsyncInjector]))
        del i
        assert all(r() is None for r in refs)


##


class Exposed:
    pass


def test_privates_collect_without_gc():
    # Private children hold their owner weakly (they are only reachable *through* it), so a privates-bearing
    # injector - child injector, its scope caches, and its provided values included - dies by pure refcount.
    with _no_gc():
        i = inj.create_injector(
            inj.private(
                inj.bind(Exposed, singleton=True, expose=True),
                inj.bind(Leaf),
            ),
        )
        v = i[Exposed]

        refs = (weakref.ref(i), weakref.ref(i[inj.AsyncInjector]), weakref.ref(v))
        del i, v
        assert all(r() is None for r in refs)


def test_wrapper_stack_collects_without_gc():
    # Wrapper stacks are privates under the hood - the same guarantee, in the real-world shape.
    with _no_gc():
        wbh = inj.wrapper_binder_helper(str)
        i = inj.create_injector(
            wbh.push_bind(to_const='hi'),
            wbh.push_bind(to_fn=inj.target(s=str)(lambda s: f'<{s}>')),
            inj.bind(inj.as_key(str, tag='out'), to_key=wbh.top),
        )
        assert i[inj.as_key(str, tag='out')] == '<hi>'

        refs = (weakref.ref(i), weakref.ref(i[inj.AsyncInjector]))
        del i
        assert all(r() is None for r in refs)


##


class GcChicken:
    def __init__(self, egg: GcEgg) -> None:
        self.egg = egg


class GcEgg:
    def __init__(self, chicken: inj.Late[GcChicken]) -> None:
        self.chicken = chicken


def test_late_does_not_pin_injector():
    with _no_gc():
        i = inj.create_injector(
            inj.bind(GcChicken, singleton=True),
            inj.bind(GcEgg, singleton=True),
            inj.bind_late(GcChicken),
        )

        chicken = i[GcChicken]
        assert chicken.egg.chicken() is chicken

        r = weakref.ref(i[inj.AsyncInjector])
        del i

        # The extracted service graph survives, but no longer pins its injector...
        assert r() is None

        # ...and a late that outlived its injector fails loudly rather than resolving stale:
        with pytest.raises(inj.DeadInjectorError):
            chicken.egg.chicken()


##


def test_steady_state_makes_no_cyclic_garbage():
    i = inj.create_injector(
        inj.bind(Leaf),
        inj.bind(Holder, singleton=True),
        inj.bind_scope(SCOPE),
        inj.bind_scope_seed(float, SCOPE),
        inj.bind(420, in_=SCOPE),
    )

    def fn(h: Holder, leaf: Leaf) -> tuple:
        return (h, leaf)

    def ops():
        i.provide(Holder)
        i.provide(Leaf)
        i.try_provide(str)
        i.inject(fn)
        with inj.enter_seeded_scope(i, SCOPE, {inj.as_key(float): 4.2}):
            i[int]
            i[float]

    for _ in range(3):
        ops()  # warm all paths (and populate global caches) before measuring

    with _no_gc():
        for _ in range(10):
            ops()
        assert gc.collect() == 0
