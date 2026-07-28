# ruff: noqa: SLF001
import asyncio
import contextvars
import gc
import threading
import weakref

import pytest

from ... import inject as inj
from ...asyncs.asynclite.promises import AsynclitePromise
from ...asyncs.asynclite.sync.api import SyncAsynclite
from ..errors import InjectorConcurrencyError
from ..impl.concurrency import ConcurrencyIdentity
from ..impl.injector import AsyncInjectorImpl
from ..impl.provision import OnceProvisionMap
from ..impl.provision import _ProvisionWaitRegistry
from ..impl.scopes import SingletonScopeImpl


def test_thread_scope_overlapping_provides():
    class Foo:
        pass

    entered = threading.Event()
    release = threading.Event()
    calls = []

    def make_foo() -> Foo:
        calls.append(threading.get_ident())
        if len(calls) == 1:
            entered.set()
            release.wait(30)
        return Foo()

    i = inj.create_injector(inj.bind(Foo, to_fn=make_foo, in_=inj.ThreadScope()))

    res: dict = {}

    def t2fn():
        entered.wait(30)
        try:
            res['t2'] = i[Foo]
        finally:
            release.set()

    t = threading.Thread(target=t2fn)
    t.start()
    try:
        res['t1'] = i[Foo]
    finally:
        t.join(30)

    assert isinstance(res['t1'], Foo)
    assert isinstance(res['t2'], Foo)
    assert res['t1'] is not res['t2']
    assert len(calls) == 2


def test_singleton_concurrent_threads():
    class Foo:
        pass

    entered = threading.Event()
    t2_ready = threading.Event()
    release = threading.Event()
    calls = []

    def make_foo() -> Foo:
        calls.append(threading.get_ident())
        entered.set()
        release.wait(30)
        return Foo()

    i = inj.create_injector(inj.bind(Foo, to_fn=make_foo, singleton=True))

    res: dict = {}

    def t1fn():
        res['t1'] = i[Foo]

    def t2fn():
        t2_ready.set()
        res['t2'] = i[Foo]

    t1 = threading.Thread(target=t1fn)
    t2 = threading.Thread(target=t2fn)
    t1.start()
    try:
        assert entered.wait(30)
        t2.start()
        assert t2_ready.wait(30)
    finally:
        release.set()
    t1.join(30)
    t2.join(30)

    assert res['t1'] is res['t2']
    assert len(calls) == 1


def test_singleton_failure_not_cached():
    class FooError(Exception):
        pass

    class Foo:
        pass

    calls = []

    def make_foo() -> Foo:
        calls.append(1)
        if len(calls) == 1:
            raise FooError
        return Foo()

    i = inj.create_injector(inj.bind(Foo, to_fn=make_foo, singleton=True))

    with pytest.raises(FooError):
        i[Foo]

    foo = i[Foo]
    assert foo is i[Foo]
    assert len(calls) == 2


def test_singleton_concurrent_failure_retry():
    class FooError(Exception):
        pass

    class Foo:
        pass

    entered = threading.Event()
    t2_ready = threading.Event()
    release = threading.Event()
    calls = []

    def make_foo() -> Foo:
        calls.append(threading.get_ident())
        if len(calls) == 1:
            entered.set()
            release.wait(30)
            raise FooError
        return Foo()

    i = inj.create_injector(inj.bind(Foo, to_fn=make_foo, singleton=True))

    res: dict = {}

    def t1fn():
        try:
            res['t1'] = i[Foo]
        except FooError as e:
            res['t1'] = e

    def t2fn():
        t2_ready.set()
        res['t2'] = i[Foo]

    t1 = threading.Thread(target=t1fn)
    t2 = threading.Thread(target=t2fn)
    t1.start()
    try:
        assert entered.wait(30)
        t2.start()
        assert t2_ready.wait(30)
    finally:
        release.set()
    t1.join(30)
    t2.join(30)

    assert isinstance(res['t1'], FooError)
    assert isinstance(res['t2'], Foo)
    assert len(calls) == 2


def test_seeded_scope_concurrent_threads():
    class Foo:
        pass

    ss = inj.SeededScope('s')

    entered = threading.Event()
    t2_ready = threading.Event()
    release = threading.Event()
    calls = []

    def make_foo() -> Foo:
        calls.append(threading.get_ident())
        entered.set()
        release.wait(30)
        return Foo()

    i = inj.create_injector(
        inj.bind_scope(ss),
        inj.bind(Foo, to_fn=make_foo, in_=ss),
    )

    res: dict = {}

    def t1fn():
        res['t1'] = i[Foo]

    def t2fn():
        t2_ready.set()
        res['t2'] = i[Foo]

    with inj.enter_seeded_scope(i, ss, {}):
        t1 = threading.Thread(target=t1fn)
        t2 = threading.Thread(target=t2fn)
        t1.start()
        try:
            assert entered.wait(30)
            t2.start()
            assert t2_ready.wait(30)
        finally:
            release.set()
        t1.join(30)
        t2.join(30)

    assert res['t1'] is res['t2']
    assert len(calls) == 1


@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('use_asyncio', [True, False])
async def test_singleton_concurrent_tasks(use_asyncio):
    class Bar:
        pass

    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []

    async def make_bar() -> Bar:
        calls.append(1)
        entered.set()
        await release.wait()
        return Bar()

    bindings: list = [
        inj.bind(Bar, to_async_fn=make_bar, singleton=True),
    ]

    if use_asyncio:
        ai = await inj.create_asyncio_injector(*bindings)
    else:
        ai = await inj.create_async_injector(*bindings)

    task1: asyncio.Future = asyncio.ensure_future(ai.provide(Bar))
    await entered.wait()
    task2: asyncio.Future = asyncio.ensure_future(ai.provide(Bar))
    for _ in range(10):
        await asyncio.sleep(0)  # let task2 reach the promise wait
    release.set()

    b1 = await task1
    if use_asyncio:
        b2 = await task2
        assert b1 is b2
    else:
        with pytest.raises(InjectorConcurrencyError):
            await task2
    assert len(calls) == 1


@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('use_asyncio', [True, False])
async def test_concurrent_requests_do_not_share_unscoped(use_asyncio):
    class C:
        pass

    class A:
        def __init__(self, c: C) -> None:
            self.c = c

    class B:
        def __init__(self, c: C) -> None:
            self.c = c

    entered = asyncio.Event()
    release = asyncio.Event()

    async def make_a(c: C) -> A:
        entered.set()
        await release.wait()
        return A(c)

    bindings: list = [
        inj.bind(C),
        inj.bind(A, to_async_fn=make_a),
        inj.bind(B),
    ]

    if use_asyncio:
        ai = await inj.create_asyncio_injector(*bindings)
    else:
        ai = await inj.create_async_injector(*bindings)

    task1: asyncio.Future = asyncio.ensure_future(ai.provide(A))
    await entered.wait()
    b = await ai.provide(B)
    release.set()
    a = await task1

    assert a.c is not b.c

    b2 = await ai.provide(B)
    assert b.c is not b2.c


def test_uncontended_singleton_promise_not_allocated():
    class Foo:
        pass

    seen: list = []

    def make_foo(i: inj.Injector) -> Foo:
        ai = i[inj.AsyncInjector]
        assert isinstance(ai, AsyncInjectorImpl)
        ssi = ai.get_scope_impl(inj.Singleton())
        assert isinstance(ssi, SingletonScopeImpl)
        (e,) = ssi._om._dct.values()
        assert isinstance(e, OnceProvisionMap._Entry)
        seen.append(e.promise)
        return Foo()

    i = inj.create_injector(inj.bind(Foo, to_fn=make_foo, singleton=True))
    i[Foo]
    assert seen == [None]


def test_completed_singleton_entry_is_terminal():
    class Foo:
        pass

    i = inj.create_injector(inj.bind(Foo, singleton=True))
    foo = i[Foo]

    ai = i[inj.AsyncInjector]
    assert isinstance(ai, AsyncInjectorImpl)
    assert ai._init_owner is None

    ssi = ai.get_scope_impl(inj.Singleton())
    assert isinstance(ssi, SingletonScopeImpl)
    (e,) = ssi._om._dct.values()
    assert isinstance(e, OnceProvisionMap._Done)
    assert e.v is foo
    assert i[Foo] is foo


def test_failed_init_marks_injector_dead():
    class FooError(Exception):
        pass

    grabbed: list = []

    def f(i: inj.Injector) -> int:
        grabbed.append(i)
        return 420

    def g(i: int) -> str:
        raise FooError

    with pytest.raises(FooError):
        inj.create_injector(
            inj.bind(f, eager=-1),
            inj.bind(g, eager=0),
        )

    i = grabbed[0]
    for _ in range(2):
        with pytest.raises(inj.DeadInjectorError) as ei:
            i.provide(int)
        assert isinstance(ei.value.__cause__, FooError)


def test_failed_init_concurrent_waiter():
    class FooError(Exception):
        pass

    grabbed: list = []
    entered = threading.Event()
    t2_ready = threading.Event()

    def f(i: inj.Injector) -> int:
        grabbed.append(i)
        entered.set()
        t2_ready.wait(30)
        raise FooError

    res: dict = {}

    def t2fn():
        entered.wait(30)
        t2_ready.set()
        try:
            res['t2'] = grabbed[0].provide(int)
        except inj.DeadInjectorError as e:
            res['t2'] = e

    t2 = threading.Thread(target=t2fn)
    t2.start()
    try:
        with pytest.raises(FooError):
            inj.create_injector(inj.bind(f, eager=True))
    finally:
        t2.join(30)

    assert isinstance(res['t2'], inj.DeadInjectorError)
    assert isinstance(res['t2'].__cause__, FooError)


def test_uncontended_init_promise_not_allocated():
    seen: list = []

    def f(i: inj.Injector) -> int:
        ai = i[inj.AsyncInjector]
        assert isinstance(ai, AsyncInjectorImpl)
        seen.append(ai._init_promise)
        return 420

    i = inj.create_injector(inj.bind(f, eager=True))

    assert seen == [None]

    ai = i[inj.AsyncInjector]
    assert isinstance(ai, AsyncInjectorImpl)
    assert ai._is_initialized
    assert ai._init_owner is None
    assert ai._init_promise is None

    assert i.provide(int) == 420


def test_concurrent_init_waiter():
    grabbed: list = []
    entered = threading.Event()
    t2_ready = threading.Event()

    def f(i: inj.Injector) -> int:
        grabbed.append(i)
        entered.set()
        t2_ready.wait(30)
        return 420

    res: dict = {}

    def t2fn():
        entered.wait(30)
        t2_ready.set()
        res['t2'] = grabbed[0].provide(int)

    t2 = threading.Thread(target=t2fn)
    t2.start()
    try:
        i = inj.create_injector(inj.bind(f, eager=True, singleton=True))
    finally:
        t2.join(30)

    assert res['t2'] == 420
    assert i.provide(int) == 420


def test_context_residue_does_not_pin_injector():
    class Foo:
        pass

    captured: list = []

    def make_foo() -> Foo:
        captured.append(contextvars.copy_context())
        return Foo()

    i = inj.create_injector(inj.bind(Foo, to_fn=make_foo))
    i[Foo]

    ai_wr = weakref.ref(i[inj.AsyncInjector])
    del i
    gc.collect()  # the injector holds itself via its internal consts

    assert captured
    assert ai_wr() is None


def test_wait_registry_walk():
    reg = _ProvisionWaitRegistry()
    k1 = inj.as_key(int)
    k2 = inj.as_key(str)
    p2: AsynclitePromise = SyncAsynclite().make_promise()
    o1 = ConcurrencyIdentity((1, None))
    o2 = ConcurrencyIdentity((2, None))

    # Self-cycle: o1 re-arriving at its own in-flight construction.
    with pytest.raises(inj.CyclicDependencyError) as ei:
        reg._detect(o1, k1, o1)
    assert ei.value.chain == (k1,)

    # Two-context cycle: o1 waits on k2 owned by o2, and o2 then wants k1 owned by o1.
    reg._waits[o1] = _ProvisionWaitRegistry._Wait(k2, p2, o2)
    with pytest.raises(inj.CyclicDependencyError) as ei:
        reg._detect(o2, k1, o1)
    assert ei.value.chain == (k1, k2)

    # A done promise's edge is treated as absent - the wait is already unwinding.
    p2.set_value(None)
    reg._detect(o2, k1, o1)


def test_cross_context_cycle_threads():
    class A:
        pass

    class B:
        pass

    a_entered = threading.Event()
    b_entered = threading.Event()

    def make_a(i: inj.Injector) -> A:
        a_entered.set()
        assert b_entered.wait(30)
        i.provide(B)
        return A()

    def make_b(i: inj.Injector) -> B:
        b_entered.set()
        assert a_entered.wait(30)
        i.provide(A)
        return B()

    i = inj.create_injector(
        inj.bind(A, to_fn=make_a, singleton=True),
        inj.bind(B, to_fn=make_b, singleton=True),
    )

    res: dict = {}

    def t1fn():
        try:
            res['t1'] = i[A]
        except inj.CyclicDependencyError as e:
            res['t1'] = e

    def t2fn():
        try:
            res['t2'] = i[B]
        except inj.CyclicDependencyError as e:
            res['t2'] = e

    t1 = threading.Thread(target=t1fn)
    t2 = threading.Thread(target=t2fn)
    t1.start()
    t2.start()
    t1.join(30)
    t2.join(30)

    assert isinstance(res['t1'], inj.CyclicDependencyError)
    assert isinstance(res['t2'], inj.CyclicDependencyError)


@pytest.mark.asyncs('asyncio')
@pytest.mark.parametrize('use_asyncio', [True, False])
async def test_cross_context_cycle_tasks(use_asyncio):
    class A:
        pass

    class B:
        pass

    a_entered = asyncio.Event()
    b_entered = asyncio.Event()

    async def make_a(i: inj.AsyncInjector) -> A:
        a_entered.set()
        await b_entered.wait()
        await i.provide(B)
        return A()

    async def make_b(i: inj.AsyncInjector) -> B:
        b_entered.set()
        await a_entered.wait()
        await i.provide(A)
        return B()

    bindings: list = [
        inj.bind(A, to_async_fn=make_a, singleton=True),
        inj.bind(B, to_async_fn=make_b, singleton=True),
    ]

    if use_asyncio:
        ai = await inj.create_asyncio_injector(*bindings)
    else:
        ai = await inj.create_async_injector(*bindings)

    rs = await asyncio.gather(ai.provide(A), ai.provide(B), return_exceptions=True)

    assert isinstance(rs[0], inj.CyclicDependencyError)
    if use_asyncio:
        assert isinstance(rs[1], inj.CyclicDependencyError)
    else:
        assert isinstance(rs[1], inj.InjectorConcurrencyError)
