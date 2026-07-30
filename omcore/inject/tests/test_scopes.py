import asyncio
import contextvars
import threading

import pytest

from ... import inject as inj
from ..impl.injector import AsyncInjectorImpl
from ..impl.scopes import DelimitedScopeImpl


def test_dupe_scope_bindings():
    ss = inj.DelimitedScope('hi')
    i = inj.create_injector(
        inj.as_elements(
            inj.bind_scope(ss),
            inj.bind(420, in_=ss),
        ),
        inj.as_elements(
            inj.bind_scope(ss),
            inj.bind('four twenty', in_=ss),
        ),
    )
    with inj.enter_scope(i, ss, {}):
        assert i[int] == 420
        assert i[str] == 'four twenty'


def test_scopes():
    ss = inj.DelimitedScope('hi')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind(420, in_=ss),
        inj.bind_scope_seed(float, ss),
    )
    with inj.enter_scope(i, ss, {
        inj.as_key(float): 4.2,
    }):
        assert i[int] == 420
        assert i[float] == 4.2


def _freeze_scope(i, ss):
    # Freezing is (currently, deliberately) impl-level api:
    ai = i[inj.AsyncInjector]
    assert isinstance(ai, AsyncInjectorImpl)
    ssi = ai.get_scope_impl(ss)
    assert isinstance(ssi, DelimitedScopeImpl)
    ssi.freeze()


def test_delimited_scope_freeze():
    ss = inj.DelimitedScope('freezer')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.bind(420, tag='a', in_=ss),
        inj.bind(421, tag='b', in_=ss),
    )

    with inj.enter_scope(i, ss, {inj.as_key(float): 4.2}):
        assert i[inj.as_key(int, tag='a')] == 420

        _freeze_scope(i, ss)

        # Provisions made before the freeze keep serving, as do seeds - but new construction is rejected:
        assert i[inj.as_key(int, tag='a')] == 420
        assert i[float] == 4.2
        with pytest.raises(inj.ScopeFrozenError):
            i.provide(inj.as_key(int, tag='b'))

    # The next opening starts fresh and unfrozen:
    with inj.enter_scope(i, ss, {inj.as_key(float): 5.3}):
        assert i[inj.as_key(int, tag='b')] == 421

    # Freezing requires an open scope:
    with pytest.raises(inj.ScopeNotOpenError):
        _freeze_scope(i, ss)


def test_delimited_eager():
    c = 0

    def foo(i: int) -> str:
        nonlocal c
        c += 1
        return f'foo: {c} {i}'

    ss = inj.DelimitedScope('hi')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind(420, in_=ss),
        inj.bind(foo, in_=ss, eager=True),
        inj.bind_scope_seed(float, ss),
    )
    assert c == 0
    with inj.enter_scope(i, ss, {
        inj.as_key(float): 4.2,
    }):
        assert c == 1
        assert i[int] == 420
        assert i[float] == 4.2
        assert i[str] == 'foo: 1 420'


##


def test_unregistered_scope_rejected():
    # A binding in a never-registered scope - not local, not in any ancestor - is rejected at injector creation, not
    # left to die with a raw KeyError at provision time.
    with pytest.raises(inj.ScopeNotRegisteredError):
        inj.create_injector(inj.bind(420, in_=inj.DelimitedScope('never-registered')))


def test_child_scope_redeclaration_rejected():
    # A child redeclaring an ancestor's scope would get its own independent state, silently shadowing the ancestor's.
    # 'Overriding scopes' is not a supported concept - fail loud.
    ss = inj.DelimitedScope('redecl')
    parent = inj.create_injector(inj.bind_scope(ss))

    with pytest.raises(inj.ScopeAlreadyRegisteredError):
        inj.create_injector(inj.bind_scope(ss), parent=parent)

    # Defaults count too - every injector already carries them:
    with pytest.raises(inj.ScopeAlreadyRegisteredError):
        inj.create_injector(inj.bind_scope(inj.ThreadScope()), parent=parent)

    # But a child declaring its *own* scope is fine, as are sibling children independently declaring the same scope:
    other = inj.DelimitedScope('child-own')
    cs = [inj.create_injector(inj.bind_scope(other), inj.bind(420, in_=other), parent=parent) for _ in range(2)]
    for c in cs:
        with inj.enter_scope(c, other, {}):
            assert c[int] == 420


##


class AncLeaf:
    pass


def test_child_binding_into_ancestor_scope():
    # Children may bind *into* an ancestor's scope: the binding lives in the child, but provisions into the
    # scope-owning ancestor's per-opening state - one opening spans the whole tree.
    ss = inj.DelimitedScope('anc')
    parent = inj.create_injector(inj.bind_scope(ss), inj.bind(420, in_=ss))
    child = inj.create_injector(inj.bind(AncLeaf, in_=ss), parent=parent)

    with pytest.raises(inj.ScopeNotOpenError):
        child.provide(AncLeaf)

    with inj.enter_scope(child, ss, {}):  # entering via the child resolves the owner's Manager
        assert child[int] == 420
        a1 = child[AncLeaf]
        assert child[AncLeaf] is a1  # cached per opening, in the owner's state

    with inj.enter_scope(parent, ss, {}):
        assert child[AncLeaf] is not a1  # each opening starts fresh


class PrivReqThing:
    def __init__(self, f: float) -> None:
        self.f = f


def test_private_binding_into_owner_scope():
    # The real usecase: a private module contributing scoped machinery to its owner's scope - its seed dependencies
    # resolving through the owner as usual.
    ss = inj.DelimitedScope('own')
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
        inj.private(
            inj.bind(PrivReqThing, in_=ss, expose=True),
        ),
    )

    with inj.enter_scope(i, ss, {inj.as_key(float): 4.2}):
        v = i[PrivReqThing]
        assert v.f == 4.2
        assert i[PrivReqThing] is v

    with inj.enter_scope(i, ss, {inj.as_key(float): 5.2}):
        assert (v2 := i[PrivReqThing]) is not v
        assert v2.f == 5.2


def test_child_eager_into_ancestor_scope_rejected():
    # Eagers must be scope-local: the owner's openings cannot see a descendant's eagers, so one could never fire.
    ss = inj.DelimitedScope('eag')
    parent = inj.create_injector(inj.bind_scope(ss))
    with pytest.raises(inj.ScopeEagerNonLocalError):
        inj.create_injector(inj.bind(AncLeaf, in_=ss, eager=True), parent=parent)


##


# One module-level var - per contextvars best practice - deliberately shared by every contextual scope below:
# its contents are opaque snapshot maps keyed by per-(scope, injector) store, so sharing is always safe.
_SCOPES_VAR: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._SCOPES_VAR')


def test_contextvar_scope_concurrent_openings():
    # With a ContextVarScopeContext, openings are context-local: concurrent asyncio tasks each open the *same* scope
    # on one shared injector, fully isolated - the RequestScope shape.
    ss = inj.DelimitedScope('cv-req', context=inj.ContextVarScopeContext(_SCOPES_VAR))

    async def main():
        i = await inj.create_asyncio_injector(
            inj.bind_scope(ss),
            inj.bind_scope_seed(float, ss),
            inj.bind(PrivReqThing, in_=ss),
        )

        gate = asyncio.Barrier(2)

        async def worker(f: float) -> None:
            async with inj.async_enter_scope(i, ss, {inj.as_key(float): f}):
                v1 = await i.provide(PrivReqThing)
                await gate.wait()  # both openings now provably concurrent
                v2 = await i.provide(PrivReqThing)
                assert v2 is v1  # cached per *this context's* opening
                assert v1.f == f  # this opening's seed, not the other's

        await asyncio.gather(worker(1.0), worker(2.0))

        # Neither opening leaked into this (parent) context:
        with pytest.raises(inj.ScopeNotOpenError):
            await i.provide(PrivReqThing)

    asyncio.run(main())


def test_contextvar_scope_task_inherits_opening():
    # Contextvar propagation applies: a task spawned *within* an opening inherits it, and shares its state.
    ss = inj.DelimitedScope('cv-inherit', context=inj.ContextVarScopeContext(_SCOPES_VAR))

    async def main():
        i = await inj.create_asyncio_injector(
            inj.bind_scope(ss),
            inj.bind(PrivReqThing, in_=ss),
            inj.bind(4.2),
        )

        async with inj.async_enter_scope(i, ss):
            v = await i.provide(PrivReqThing)
            assert (await asyncio.ensure_future(i.provide(PrivReqThing))) is v

    asyncio.run(main())


def test_contextvar_scope_sync_and_threads():
    # The sync facade works transparently (sync_await drives coroutines in the calling context), and raw threads are
    # their own contexts: each may hold its own opening, and one with none gets ScopeNotOpenError - loudly, rather
    # than silently reading another actor's request.
    ss = inj.DelimitedScope('cv-sync', context=inj.ContextVarScopeContext(_SCOPES_VAR))
    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind_scope_seed(float, ss),
    )

    with inj.enter_scope(i, ss, {inj.as_key(float): 4.2}):
        assert i[float] == 4.2

        errs: list = []

        def unopened():
            try:
                i.provide(float)
            except inj.ScopeNotOpenError as e:
                errs.append(e)

        t = threading.Thread(target=unopened)
        t.start()
        t.join()
        assert len(errs) == 1

        res: list = []

        def opened():
            with inj.enter_scope(i, ss, {inj.as_key(float): 5.2}):
                res.append(i[float])

        t2 = threading.Thread(target=opened)
        t2.start()
        t2.join()
        assert res == [5.2]

        assert i[float] == 4.2  # the main thread's opening, undisturbed throughout

    with pytest.raises(inj.ScopeNotOpenError):
        i.provide(float)


def test_contextvar_scope_reentry_rejected():
    # Same-context reentry is still an error - contextual openings do not nest:
    ss = inj.DelimitedScope('cv-re', context=inj.ContextVarScopeContext(_SCOPES_VAR))
    i = inj.create_injector(inj.bind_scope(ss))

    with inj.enter_scope(i, ss):
        with pytest.raises(inj.ScopeAlreadyOpenError):  # noqa
            with inj.enter_scope(i, ss):
                pass


def test_contextvar_scope_shared_var():
    # The sharing property, exercised deliberately: two scopes on one injector backed by one var, with *non-LIFO*
    # interleaved openings in a single context - closing the first does not clobber the second (close is explicit
    # snapshot removal, not token-reset)...
    sa = inj.DelimitedScope('cv-share-a', context=inj.ContextVarScopeContext(_SCOPES_VAR))
    sb = inj.DelimitedScope('cv-share-b', context=inj.ContextVarScopeContext(_SCOPES_VAR))
    i = inj.create_injector(
        inj.bind_scope(sa),
        inj.bind_scope_seed(float, sa),
        inj.bind_scope(sb),
        inj.bind_scope_seed(str, sb),
    )

    cma = inj.enter_scope(i, sa, {inj.as_key(float): 4.2})
    cmb = inj.enter_scope(i, sb, {inj.as_key(str): 'yo'})
    cma.__enter__()
    cmb.__enter__()
    try:
        assert i[float] == 4.2
        assert i[str] == 'yo'
    finally:
        cma.__exit__(None, None, None)  # non-LIFO: a closes first

    try:
        assert i[str] == 'yo'  # b's opening survives a's close
        with pytest.raises(inj.ScopeNotOpenError):
            i.provide(float)
    finally:
        cmb.__exit__(None, None, None)

    # ...and likewise across *injectors*: same scope, same var, one context, independent states:
    i2 = inj.create_injector(inj.bind_scope(sa), inj.bind_scope_seed(float, sa))
    with inj.enter_scope(i, sa, {inj.as_key(float): 1.0}), inj.enter_scope(i2, sa, {inj.as_key(float): 2.0}):
        assert i[float] == 1.0
        assert i2[float] == 2.0
