"""
Tests for the (impl-level) provision-plan compiler: parity with interpreted semantics, the
mirroring decisions, and cross-boundary coherence. See impl/plans.py.
"""
import asyncio
import contextvars
import typing as ta

import pytest

from ... import inject as inj
from ... import lang
from ..impl.plans import ProvisionPlan
from ..impl.plans import ProvisionPlanCompiler
from ..impl.plans import compile_provision_plan


##


def _provide(p: ProvisionPlan, i: ta.Any) -> ta.Any:
    # Plans are async-native - drive them as the sync facade drives everything else:
    return lang.sync_await(p.provide(i))


class Leaf:
    pass


class Left:
    def __init__(self, leaf: Leaf) -> None:
        self.leaf = leaf


class Right:
    def __init__(self, leaf: Leaf) -> None:
        self.leaf = leaf


class Root:
    def __init__(self, left: Left, right: Right) -> None:
        self.left = left
        self.right = right


def test_diamond_memoization():
    # Diamond sharing within one execution, fresh across executions - interpreted request-memo semantics:
    ce = inj.collect_elements(inj.as_elements(
        inj.bind(Leaf),
        inj.bind(Left),
        inj.bind(Right),
        inj.bind(Root),
    ))
    i = inj.create_injector(ce)
    p = compile_provision_plan(ce, Root)

    assert p.is_closed

    r = _provide(p, i)
    assert r.left.leaf is r.right.leaf
    assert _provide(p, i).left.leaf is not r.left.leaf


def test_singleton_cache_shared_with_interpreter():
    # Plans must be compiled against the *same* collection the injector runs - BindingImpl identity keys the scope
    # caches - and then the caches are fully shared, in both directions:
    ce = inj.collect_elements(inj.as_elements(inj.bind(Leaf, singleton=True)))
    i = inj.create_injector(ce)
    p = compile_provision_plan(ce, Leaf)

    first = _provide(p, i)
    assert i[Leaf] is first

    i2 = inj.create_injector(ce)
    second = i2[Leaf]
    assert _provide(p, i2) is second  # one plan serves any injector over the collection


def test_delimited_scope():
    ss = inj.DelimitedScope('plans-test')
    ce = inj.collect_elements(inj.as_elements(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.bind(str, in_=ss, to_fn=inj.target(f=float)(lambda f: f'f={f}')),
        inj.bind(int, in_=ss, to_fn=inj.target()(lambda: 420)),
    ))
    i = inj.create_injector(ce)
    p = compile_provision_plan(ce, str)

    with pytest.raises(inj.ScopeNotOpenError):
        _provide(p, i)

    with inj.enter_scope(i, ss, {inj.as_key(float): 4.2}):
        v = _provide(p, i)
        assert v == 'f=4.2'
        assert _provide(p, i) is v  # cached per opening
        assert i[str] is v  # the interpreter sees the plan-filled scope cache

    with inj.enter_scope(i, ss, {inj.as_key(float): 5.2}):
        assert _provide(p, i) == 'f=5.2'  # fresh per opening


def test_cycles_detected_at_compile_time():
    ce = inj.collect_elements(inj.as_elements(
        inj.bind(str, to_fn=inj.target(x=int)(lambda x: '')),
        inj.bind(int, to_fn=inj.target(x=str)(lambda x: 0)),
    ))
    with pytest.raises(inj.CyclicDependencyError):
        compile_provision_plan(ce, str)


def test_unbound_key_raises():
    ce = inj.collect_elements(inj.as_elements(inj.bind(420)))
    i = inj.create_injector(ce)
    with pytest.raises(inj.UnboundKeyError):
        _provide(compile_provision_plan(ce, str), i)


def test_listener_fallback():
    async def exclaim(injector: ta.Any, key: ta.Any, binding: ta.Any, fn: ta.Any) -> ta.Any:
        v = await fn()
        return v + '!' if isinstance(v, str) else v

    ce = inj.collect_elements(inj.as_elements(
        inj.bind('hi'),
        inj.bind_provision_listener(exclaim),
    ))
    i = inj.create_injector(ce)
    assert _provide(compile_provision_plan(ce, str), i) == 'hi!'


def test_parent_delegation_via_hole():
    # One compiled plan over the child collection serves any child of any parent, parent-bound deps included:
    pce = inj.collect_elements(inj.as_elements(inj.bind(Leaf, singleton=True)))
    cce = inj.collect_elements(inj.as_elements(inj.bind(Left)))
    p = compile_provision_plan(cce, Left)
    assert not p.is_closed

    for _ in range(2):
        parent = inj.create_injector(pce)
        child = inj.create_injector(cce, parent=parent)
        assert _provide(p, child).leaf is parent[Leaf]


##


class BoundaryB:
    def __init__(self, leaf: Leaf) -> None:
        self.leaf = leaf


class CompiledFirstRoot:
    def __init__(self, leaf: Leaf, b: BoundaryB) -> None:
        self.leaf = leaf
        self.b = b


class HoleFirstRoot:
    def __init__(self, b: BoundaryB, leaf: Leaf) -> None:
        self.b = b
        self.leaf = leaf


async def _make_boundary_b(leaf: Leaf) -> BoundaryB:
    return BoundaryB(leaf)


def _boundary_ce(root_cls: type) -> ta.Any:
    return inj.collect_elements(inj.as_elements(
        inj.bind(Leaf),
        inj.bind(BoundaryB, to_async_fn=_make_boundary_b),  # async: a hole
        inj.bind(root_cls),
    ))


def test_cross_boundary_coherence_compiled_first():
    # An unscoped dep shared by a compiled node and an interpreted hole is one instance per request - the compiled
    # value is *written* to the ambient request, where the hole's interpreter finds it:
    ce = _boundary_ce(CompiledFirstRoot)
    i = inj.create_injector(ce)
    p = compile_provision_plan(ce, CompiledFirstRoot)
    assert not p.is_closed

    r = _provide(p, i)
    assert r.b.leaf is r.leaf


def test_cross_boundary_coherence_hole_first():
    # ...and in the other direction: a value the hole's interpreter constructed first is *read* from the ambient
    # request by the compiled node, rather than recomputed:
    ce = _boundary_ce(HoleFirstRoot)
    i = inj.create_injector(ce)
    p = compile_provision_plan(ce, HoleFirstRoot)

    r = _provide(p, i)
    assert r.b.leaf is r.leaf


def test_compiler_reuse_shares_subtrees():
    ce = inj.collect_elements(inj.as_elements(
        inj.bind(Leaf, singleton=True),
        inj.bind(Left),
        inj.bind(Right),
    ))
    i = inj.create_injector(ce)
    c = ProvisionPlanCompiler(ce)
    pl, pr = c.compile(Left), c.compile(Right)
    assert _provide(pl, i).leaf is _provide(pr, i).leaf  # via the shared singleton


##


async def _make_async_leaf() -> Leaf:
    return Leaf()


_AIO_VAR: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._AIO_VAR')


def test_asyncio_fast_path():
    # Plans are async-native: under event-loop concurrency the fast path engages too, and genuinely-suspending
    # holes (an async provider) are awaited in the loop rather than sync-driven:
    ss = inj.DelimitedScope('plans-aio', context=inj.ContextVarScopeContext(_AIO_VAR))
    ce = inj.collect_elements(inj.as_elements(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.bind(str, in_=ss, to_fn=inj.target(f=float)(lambda f: f'f={f}')),
        inj.bind(Leaf, to_async_fn=_make_async_leaf),
        inj.bind(Left),
    ))

    async def main() -> None:
        i = await inj.create_asyncio_injector(ce)

        async with inj.async_enter_scope(i, ss, {inj.as_key(float): 4.2}):
            assert (await i.provide(str)) == 'f=4.2'  # planned, scoped, under the loop

        v = await i.provide(Left)  # planned root over an async-provider hole
        assert isinstance(v.leaf, Leaf)

    asyncio.run(main())
